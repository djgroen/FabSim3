# 
# This source file is part of the FabSim software toolkit, which is distributed under the BSD 3-Clause license. 
# Please refer to LICENSE for detailed information regarding the licensing.
#
# IBI.py is an implementation of the Iterative Boltzmann Inversion procedure in Python.

import os, sys, math
import numpy as np
import scipy 
import pylab
import scipy.optimize
import lib.LammpsIO as lmp_io
import lib.DataAnalysis as da
import lib.DataMorphing as dm

def generate_interaction_list(num_of_types):
  int_set = []
  for ii in xrange(1, num_of_types+1):
    for iii in xrange(ii, num_of_types+1):
      int_set.append([ii, iii])
  return int_set
  
def interaction_list_from_file(interaction_filename):
  int_set = []
  LIST_IN = open(interaction_filename, 'r') 
  for line in LIST_IN:
    if line[0:1] != "#":
      NewRow = (line.strip()).split()
      if len(NewRow) == 2:
        int_set.append([int(NewRow[0]), int(NewRow[1])])
  LIST_IN.close()
  return int_set
#-----------------------------------------------------------------------------------------------------
   
         
def read_in_rdf_file(filename, number_of_types, interaction_list):
  """ subroutine to read in the RDF file - note, the format must be distance is first column, and RDF is the third column 
      ASSUMPTION: ALL RDF FILES HAVE THE SAME NUMBER OF BINS AND CUTOFF. """
  index = 0 
  print "reading RDF %s" % (filename)
  numofbins, cutoff, o = lmp_io.get_number_of_bins_and_cutoff("%s.1.1" % (filename), 0)
  rdf_array = np.zeros((number_of_types+1, number_of_types+1, numofbins+1)) 
 
  for i in interaction_list:
    LIST_IN = open("%s.%d.%d" % (filename, i[0], i[1]), 'r') 
    index = 0
    for line in LIST_IN:
      NewRow = (line.strip()).split()
      mystring = NewRow[0][0:1]
      if mystring != "#":
        if len(NewRow)>2:
          index += 1   
          rdf_array[i[0]][i[1]][index] = float(NewRow[2])          
    LIST_IN.close()      
  return  rdf_array, int(numofbins), float(cutoff)


def read_CG_log_file(CG_file, label="Press"):
  """ reads a lammps CG thermodynamic log file, and calculates the average pressure """
  
  print "CG LOG FILE LABEL:", label
  
  index = 0 
  pressure_total = 0 
  pressure_number = 0 
  LIST_IN = open(CG_file,'r') 
  
  for line in LIST_IN:
    if line[0] != '#':
      NewRow = (line.strip()).split()
      number_of_cols = len(NewRow) 
      for n in xrange(0, number_of_cols): 
        mystring = NewRow[n][0:len(label)]
 #       if (mystring == "Pre"):
 #         print "Pressure =", float(NewRow[n+2])
 #       if (mystring == "Pzz"):
 #         print "Pzz =", float(NewRow[n+2])
        if (mystring == label):
          #print label, len(label)
          index += 1 
          if (index > 100):
            # ignore the first 100 values 
            pressure_total  += float(NewRow[n+2])
            pressure_number += 1
  
  LIST_IN.close()
  final_pressure = pressure_total / pressure_number
  print "For %d pressure calculations of the CG system, the average pressure (%s) is %f bar" % (pressure_number, label, final_pressure) 
  return final_pressure 



def modify_lammps_in_file(in_file, out_file, number, interaction_list, num_of_types): 
  """ Create a new lammps file that will read the next iteration of potentials """
  print "modify_lammps_in_file", in_file, number, interaction_list
  count  = 0 
  NEW_FILE = open("%s.%s" % (out_file, number+1),'w+') 
#  LIST_IN  = open("%s.%s" % (in_file, number_old), 'r') 
  LIST_IN  = open("%s" % (in_file), 'r') 
  
  for line in LIST_IN:
    NewRow = (line.strip()).split() 
    if (len(NewRow) > 0):
      if NewRow[0].lower() == "pair_coeff":      
        if count < 1:
          count += 1 
          for ii in xrange(1, num_of_types+1):
            for iii in xrange(ii, num_of_types+1):
              if [ii, iii] in interaction_list:
                print "pair_coeff %d %d pot.%d.new.%d.%d TABLE_%d.%d \n" % (ii, iii, number+1, ii, iii, ii, iii)
                NEW_FILE.write("pair_coeff %d %d pot.%d.new.%d.%d TABLE_%d.%d \n" % (ii, iii, number+1, ii, iii, ii, iii)) 
              else:
                print "pair_coeff %d %d pot.converged.%d.%d TABLE_%d.%d \n" % (ii,iii,ii,iii,ii,iii)
                NEW_FILE.write("pair_coeff %d %d pot.converged.%d.%d TABLE_%d.%d \n" % (ii,iii,ii,iii,ii,iii))
      else:
        NEW_FILE.write("%s\n" % (line.strip())) 

  LIST_IN.close()
  NEW_FILE.close() # ensure files are close before using 'sed' so that buffers are written to disk.
    
  os.system("sed -i s/.%d.rdf/.%d.rdf/g %s.%d" % (number, number+1, out_file, number+1)) 
  os.system("sed -i s/prod%d/prod%d/g %s.%d" % (number, number+1, out_file, number+1))


def calc_pressure_correction(new_g_r, numofbins, DeltaR, number_of_types_ii, number_of_types_iii, scale_factor, p_now, p_target, volume, temperature):
  print "P+) Applying pressure function."
  
  pressure_pot = np.zeros((numofbins+1))
  
  # apply pressure correction if requested
  rcut = float(numofbins) * float(DeltaR)
  
  integral = 0.0
  x = 0.0
  nktv2p = 68568.415 #LAMMPS unit conversion [no. atoms per volume] -> [Bar]
  #bar_to_SI = 0.06022/4.1868 # 1bar=0.06022 kJ /(nm mol) - then converted to Kcal mol / (nm mol)
  for i in xrange(1, int(numofbins+1)):
    x = i * DeltaR
    if len(new_g_r) > i: #RDF == G(r)
      integral += x * x * x * DeltaR * new_g_r[i] #Eq. 6 Fu et al., 164106, 2012
    
  partDens_ii  = number_of_types_ii  / volume
  partDens_iii = number_of_types_iii / volume
  # integral += (delta_r / 2 * rdf_cur[max/delta_r]*max*max*max)
  #        print "pref values:"
  #        print math.pi, partDens_ii, partDens_iii, integral
  
  pref = -3 * rcut * (p_now - p_target) * 1 / nktv2p
  pref /= 2 * math.pi * partDens_ii * partDens_iii * integral
    
  # use max(pref, +-0.1kt) as prefactor 
  temp = pref
  kB = 0.0019858775
  kBT = kB * temperature #0.0019872067
  print "Pressure correction factor1: A =", pref

  if temp < 0:
    temp = -1 * temp 
  if temp > (0.1 * kBT):
    if (pref > 0):
      pref = 0.1 * kBT
    else:
      pref = -0.1 * kBT
           
  pref = pref * scale_factor
  print "Pressure correction factor: A =", pref, scale_factor    
  for i in xrange(0, numofbins+1):
    x = i * DeltaR
    pressure_pot[i] = pref * (1 - x / rcut)
  
  return pressure_pot
  
  
def update_one_file(out_path, target_g_r, new_g_r, old_distance, old_potential, num_of_types, number, DeltaR, numofbins, number_of_types1, number_of_types2,
lattice, LJ_file_flag, p_flag, p_now, p_target, temperature, atom1, atom2):
  
  number = int(number)
  potential = np.zeros((numofbins+1)) 
  derivative = np.zeros((numofbins+1))
  new_number = number + 1 
  volume = float(lattice[0]) * float(lattice[1]) * float(lattice[2])
  
  print "Lengths: ", len(target_g_r), len(new_g_r), len(old_distance), len(old_potential), numofbins
  
  index = length = 0 
  x_data = np.zeros((numofbins+1)) 
  y_data = np.zeros((numofbins+1))
  success = 0 
  # smooth the new CG radial distribution function and calculate where the old CG rdf starts (it will be zero at low distance values). 
  
  filtered_rdf = dm.smooth_data(new_g_r) 

  np.append(filtered_rdf, 1)
  
  conversion_extrapolate_tmp = {}   
  pressure_pot = np.zeros((numofbins+1))

  if abs(float(p_flag)) > 0.00001:
    print "FabMD: P+) Applying pressure function."
    pressure_pot = calc_pressure_correction(new_g_r, numofbins, DeltaR, number_of_types1, number_of_types2, abs(p_flag), p_now, p_target, volume, temperature)
  else:
    print "FabMD: P-) Not applying any pressure correction."
#      use_data = 0    

  if float(p_flag) < -0.00001:
    print "FabMD: I-) IBI is disabled!"

  pot_write_threshold = -1 # slot where we start the pot functions
  kB = 0.0019858775

  for i in xrange(0, numofbins+1):  
#        print old_distance[1], i, i*DeltaR
    if old_distance[1] <= ((i+0.1) * DeltaR): #0.1 is here to prevent tiny bugs in float comparisons, causing the list to get shorter and shorter...        
      if pot_write_threshold == -1:
        pot_write_threshold = i
      length += 1

      # the IBI update to the potential 
      target_g_r_i = 1.0
      if len(target_g_r) > i:
        target_g_r_i = target_g_r[i]
        
      fri = 1.0 #filtered rdf shorthand for beyond the cutoff.
      if len(filtered_rdf) > i:
        fri = filtered_rdf[i]

      if float(p_flag) < -0.00001: # Disable IBI part.
          print "old potential:", old_potential[length]
          print "pressure modification:", pressure_pot[i-1]
          potential[i] = old_potential[length] + pressure_pot[i-1]
    
      #print i, (abs(target_g_r_i) > 0), (fri > 0.15), i*DeltaR, old_potential[length], pressure_pot[i]
      if (abs(target_g_r_i) > 0) and (fri > 0.15):
        if float(p_flag) > -0.00001: # Enable IBI part.
          # print "FabMD: I+) IBI is enabled!"
          potential[i] = old_potential[length] + (kB * temperature) * math.log(fri / target_g_r_i) + pressure_pot[i-1] 

          
        # Debug check
        # if abs(old_distance[length] - i*DeltaR)>0.00001: 
        #  print "Error: old_distance seems to be wrongly mapped!"
        #  exit()
        
        x_data[index] = i * DeltaR 
        y_data[index] = potential[i]
        
        index += 1
        #print i, potential[i]
      else:
        # this array indicates which values we need to an extrapolation for the potential and for the forces (negative of the potential derivative) - defined as where 
        # the RDF is less than 0.15, yet is defined in the old potential file. 
        conversion_extrapolate_tmp[i] = 1       

  #exit()    
  x_data.resize((index))
  y_data.resize((index))
  dy = da.derivatives(x_data, y_data) 
    
#      print y_data, dy, len(y_data), len(dy)
#      exit()
    
  parameters = {} 
  square_residual = 0 

  if LJ_file_flag == 1:
    # read in Lennard-Jones parameters from file if requested. 
    parameters = {}
    LJ_IN = open("LJ_parameters", 'r')
    
    for line in LJ_IN:
      NewRow = (line.strip()).split()
      if (NewRow[2] == atom1) and (NewRow[3] == atom2):
        parameters[0][1] = NewRow[6]
        parameters[1][1] = NewRow[9] 
        
    LJ_IN.close()

  else:
    # fitting the potential derivative (i.e. negative forces) using CurveFit.pm to a Lennard Jones 6 - 3 potential (i.e. 7 - 4 when differentiated )       
    fitfunc = lambda p, x: - 6 * (( ( 4 * p[0] * p[1]**6) / x**7) - ( (4 * p[0] * p[1]**3) / (2*x**4)) )
    errfunc = lambda p, x, y: fitfunc(p, x) - y
    #print "X_DATA = ", x_data, dy, y_data

    p0 = np.array([0.5, 4.5]) #was 0.5,4.5
    p1, success = scipy.optimize.leastsq(errfunc, p0[:], maxfev=5000, args=(x_data, dy)) #use [:int(4.0/DeltaR)] to optimize up to a cutoff of 4.
    
    if success == 0:
      print "Scipy.optimize did not manage to converge the fit on dataset", atom1, atom2, "! Exiting now."
      exit()

    LJ_OUT = open("%s/LJ_parameters" % (out_path),'w') 
    LJ_OUT.write("LJ PARAMETERS %d %d p0 = %f, p1 = %f\n" % (atom1, atom2, p1[0], p1[1]))      
    LJ_OUT.close()

    for i in xrange(numofbins+1, 1, -1):
      if i in conversion_extrapolate_tmp.keys(): #77-31
        #print i
        if conversion_extrapolate_tmp[i] > 0:
          new_distance = i * DeltaR
          # These Lennard-Jones forces are then numerically integrated to get the potential
          derivative[i] = -np.abs(fitfunc(p1, new_distance))
          diff = x_data[0] - new_distance
          ave = 0.5 * fitfunc(p1, new_distance) - 0.5 * dy[0]
          r_y = np.abs(y_data[0] - diff * ave)
          potential[i] = r_y
#            print i, derivative[i], potential[i], "!"

    index = 0
    for i in xrange(pot_write_threshold, numofbins+1):
      if i not in conversion_extrapolate_tmp.keys():
        derivative[i] = dy[index]
        index += 1 
    
    index = 0
    for i in xrange(0, numofbins+1):
      if len(derivative) > i:
        if abs(derivative[i]) > 0:
          index += 1 
          # determining the number of potential values

    lmp_io.write_pot_file("%s/pot.%d.new.%d.%d" % (out_path, new_number, atom1, atom2), derivative, potential, numofbins, DeltaR, atom1, atom2, index) 
    #first index was numofbins

#-----------------------------------------------------------------------------------------------------
def compute_update(out_path, target_g_r, new_g_r, old_distance, old_potential, num_of_types, number, DeltaR, numofbins, number_of_types, lattice, LJ_file_flag,
p_flag, p_now, p_target, temperature, interaction_list): 
  """ This subroutines performs the IBI. """
  print "PFlag = ", p_flag
  #go up to numofbins iters at all times!
  for i in interaction_list:
    update_one_file(out_path, target_g_r[i[0]][i[1]], new_g_r[i[0]][i[1]], old_distance[i[0]][i[1]], old_potential[i[0]][i[1]], num_of_types, number, DeltaR,
numofbins, number_of_types[i[0]], number_of_types[i[1]], lattice, LJ_file_flag, p_flag, p_now, p_target, temperature, i[0], i[1])


def apply_pressure_correction(old_potential, pressure_pot, length, threshold, DeltaR, mode="rigid"):
  """ Applies a pressure correction in a gradual way (or not!) 
  Supported modes: 
  rigid = rigid smoothing
  gradual = slowly increasing smoothing
  halfway = slowly increasing smoothing, starting at 50% threshold and ending at 150% threshold
  """
    
  threshold_num = threshold/DeltaR
    
  if mode == "rigid":
    for i in xrange (0, length):     
      potential[i] = old_potential[i] 
      if threshold <= ((i+0.1) * DeltaR): #0.1 is here to prevent tiny bugs in float comparisons, causing the list to get shorter and shorter...        
        potential[i] += pressure_pot[i]
  if mode == "gradual":
    for i in xrange (0, length):     
      potential[i] = old_potential[i] 
      
    #potential[threshold_num:length] += pressure_pot[threshold_num:length]
        
      if threshold <= ((i+0.1) * DeltaR): #0.1 is here to prevent tiny bugs in float comparisons, causing the list to get shorter and shorter...        
        potential[i] += pressure_pot[i]      
  if mode == "halfway":
    for i in xrange (0, length):     
      potential[i] = old_potential[i] 
      if threshold <= ((i+0.1) * DeltaR): #0.1 is here to prevent tiny bugs in float comparisons, causing the list to get shorter and shorter...        
        potential[i] += pressure_pot[i]            
          
  print "Sum of pressure correction: ", np.sum(np.abs(pressure_pot))
  return potential        
  
  
def production():
  """ This script will create the next interation of coarse-grained potentials using the Iterative Boltzmann Inversion to 
  match to a user-supplied radial distribution function (normally from atomistic simulation). It will also attempt a correction 
  for the pressure. The script will also extrapolate the potentials at low distance values by fitting to a soft Lennard-Jones 
  potential. Note, this fitting is somewhat unstable (CurveFit.pm) and can cause the IBI to fail. """

  print "ARGUMENTS TO THE IBI ARE: ", sys.argv 

  # user-supplied arguments to the IBI. Note, not all of these arguments are required depending on what analysis is need and files are provided. 
  lammps_input_file = "" # LAMMPS input file for the current CG iteration. 
  correct_rdf_base  = "" # User-supplied Radial Distribution Function to match to (normally derived from atomistic simulation) - distance is column 1 and the RDF is column 3.   
  potential_base    = "" # the file base-name for the potential energy files. The format is such: pot.<iteration_number>.new.<type1><type2>. In this case the base-name is "pot". 
  number = 0             # the current IBI iteration number
  lammps_data_file = ""  # LAMMPS CG data file 
  lammps_rdf_file  = ""  # the CG RDF file if calculated by LAMMPS - this is a series of snapshot values, which need to be averaged. 
  p_target = 1.0         # pressure target for the CG simulation.
  p_flag   = 0.0         # flag to indicate whether to apply pressure correction - set to one if a pressure target is set by the user. 
  CG_output_file = ""    # LAMMPS thermodynamic log file for the current CG simulation. Used to calculate the current average CG pressure. 
  p_now    = 0           # current CG pressure read from (and averaged) the CG lammps thermodynamic log file; 
  temperature = 300      # temperature the simulations are run at; default is 300K
  LJ_file_flag = 0       # if this flag is set to one, the parameters used in the extrapolation by fitting to a Lennard-Jones potential are read from a file (called LJ_parameters) rather than computed from fitting to the potential / forces.  
  num_of_bins = 0
  DeltaR = 0.0
  number_of_arguments = len(sys.argv) 
  mode = "default"
  num_of_types = 0

  for i in xrange(0, number_of_arguments):  
    if sys.argv[i].lower() == "lammps_input_file":
      lammps_input_file = sys.argv[i+1] 
      print "THE LAMMPS INPUT FILE IS ", lammps_input_file 
    elif sys.argv[i].lower() == "lammps_output_file":
      lammps_output_file = sys.argv[i+1] 
      print "THE LAMMPS OUTPUT FILE IS ", lammps_input_file 
    elif sys.argv[i].lower() == "lammps_data_file":
      lammps_data_file = sys.argv[i+1] 
      print "THE LAMMPS DATA FILE IS ", lammps_data_file
    elif ((sys.argv[i] == "potential_base") or (sys.argv[i] == "potential")):
      potential_base = sys.argv[i+1] 
    elif sys.argv[i].lower() == "lammps_rdf_file":
      lammps_rdf_file = sys.argv[i+1] 
      print "THE RDFS WILL BE READ FROM LAMMPS OUTPUT", lammps_rdf_file
    elif (sys.argv[i] == "correct_rdf_base"):
      correct_rdf_base = sys.argv[i+1] 
      print "THE RDFS TO MATCH TO HAVE THE FILE BASE ", correct_rdf_base
    elif ((sys.argv[i] == "number") or (sys.argv[i] == "current_number") or (sys.argv[i] == "iteration_number")):
      number = int(sys.argv[i+1])
      print "THE CURRENT ITERATION NUMBER IS ", number
    elif ((sys.argv[i] == "pressure_flag") or (sys.argv[i] == "p_flag")):
      p_flag = float(sys.argv[i+1])
      print "THE PRESSURE FLAG is ", p_flag
    elif ((sys.argv[i] == "pressure_target") or (sys.argv[i] == "p_target")):
      p_target = float(sys.argv[i+1])
      if abs(p_flag) < 0.00001:
        p_flag = 1 
      print "THE PRESSURE TARGET is ", p_target
    elif ((sys.argv[i] == "CG_log_file") or (sys.argv[i] == "CG_logfile")):
      CG_output_file = sys.argv[i+1] 
      p_now = read_CG_log_file(CG_output_file, label="Press")          
      #TODO: this is only a temp hack!
      print "THE CURRENT PRESSURE WILL BE CALCULATED FROM THE LOG FILE ", CG_output_file , p_now
    elif (sys.argv[i] == "temperature"):
      temperature = float(sys.argv[i+1])
    elif (sys.argv[i] == "LJ_param_file"):
      LJ_file_flag = 1
      
    elif sys.argv[i].lower() == "numofbins":
      num_of_bins = int(sys.argv[i+1]) 
      print "THE NUMBER OF BINS IS ", num_of_bins
    elif sys.argv[i].lower() == "deltar":
      DeltaR = float(sys.argv[i+1]) 
      print "DeltaR IS ", DeltaR
           
    elif sys.argv[i] == "mode":
      mode = sys.argv[i+1]
    elif sys.argv[i].lower() == "numoftypes":
      num_of_types = int(sys.argv[i+1]) 

  # read in the lammps data file to identify the number of CG types and lattice parameters. 
  lattice, type_list = lmp_io.read_lammps_data_file(lammps_data_file)

  num_of_types = len(type_list)
  print "Num of types = ", num_of_types
  #num_of_types = 4
   
  number_of_types_array = np.zeros((num_of_types+1))
  for n in xrange(1, num_of_types+1):
    number_of_types_array[n] = len(type_list["%s" % n]) 

  if mode=="pressure_correct":
    
    num_of_bins, cutoff, offset = lmp_io.get_number_of_bins_and_cutoff(potential_base, 1)
    print "Potential numofbins and cutoff:", num_of_bins, cutoff
    
    pots = (potential_base.strip()).split('.')
    atom1 = int(pots[-2])
    atom2 = int(pots[-1])
    
    print "ATOMS are:", atom1, atom2
    
    potential = np.zeros((num_of_bins+1)) 
    volume = float(lattice[0]) * float(lattice[1]) * float(lattice[2])
      
    hist_rdf = lmp_io.read_lammps_rdf(lammps_rdf_file, num_of_types, number)
   
    pressure_pot = calc_pressure_correction(hist_rdf[atom1][atom2], num_of_bins, DeltaR, number_of_types_array[atom1], number_of_types_array[atom2], abs(p_flag), p_now, p_target, volume, temperature)

    old_distance, old_potential, old_derivative = lmp_io.read_in_interaction_file(potential_base, num_of_bins)
   
    potential = apply_pressure_correction(old_potential, pressure_pot, num_of_bins+1, old_distance[1], DeltaR)
        
    potential[0]=potential[1] # TODO: change this temporary workaround into something more systematic. The workaround reduces anomalies in the derivative at the start of the potential.   
    new_derivatives = da.derivatives(np.arange(offset, cutoff, DeltaR), potential)
    print "dy lens:", num_of_bins, len(new_derivatives), len(np.arange(offset-DeltaR, cutoff, DeltaR)), len(potential)
    
    write_pot_file("%s/pot.%d.new.%d.%d" % (os.path.dirname(lammps_output_file), number+1, atom1, atom2), new_derivatives[1:] , potential[1:], num_of_bins, DeltaR, atom1, atom2, num_of_bins, offset, smoothing="no", selection="no") #note: we use an offset here!
    
    
    
  elif mode=="default":
    # Either read an interaction list from a file in the atom_dir (useful if you want to parametrize only a subset of interactions), or generate one on the fly.
    interaction_filename = os.path.dirname(correct_rdf_base) + "/interaction_list"
    if os.path.exists(interaction_filename):
      interaction_list = interaction_list_from_file(interaction_filename)
    else: 
      interaction_list = generate_interaction_list(num_of_types)
       
    first_array, num_of_bins, cutoff2 = read_in_rdf_file(correct_rdf_base, num_of_types, interaction_list) # read in the rdfs to match to. 

    print "THE CUTOFF in the RDF files is", cutoff2, ", with", len(first_array[1][1])-1, "number of bins "; 
    print "THIS IS ITERATION NUMBER", number

    deltaR = cutoff2 / num_of_bins # bin spacing from the RDF 
    previous_position, previous_potential, previous_derivative, old_pot_files, cutoff = lmp_io.read_in_interaction_files(potential_base, num_of_types,
interaction_list, number)
    num_of_bins = int(cutoff / deltaR)

    print deltaR, cutoff2, num_of_bins, correct_rdf_base
    print "THE CUTOFF in the POS FILES is", cutoff, "and number of bins are", num_of_bins 

    # read in the RDFs of the CG calculated by LAMMPS.
    hist_rdf = lmp_io.read_lammps_rdf(lammps_rdf_file, num_of_types, number)
  #  print lammps_rdf_file, len(hist_rdf[1][1])
    DeltaR = cutoff / num_of_bins
    
    # calculate the IBI 
    compute_update(os.path.dirname(lammps_output_file), first_array, hist_rdf, previous_position, previous_potential, num_of_types, number, DeltaR, num_of_bins, number_of_types_array, lattice, LJ_file_flag, p_flag, p_now, p_target, temperature, interaction_list)
    # modify the lammps input file, ready for the next iteration
    modify_lammps_in_file(lammps_input_file, lammps_output_file, number, interaction_list, num_of_types)
  else:
    print "ERROR: mode is incorrectly set in IBI.py. Should be e.g., default or pressure_correct"
    sys.exit()

def basic_test_suite():
  """ Simple testing of various functions in the script."""
  print "read_lammps_data_file"
  lattice, type_list = lmp_io.read_lammps_data_file("CG_first_interaction.lammps05")
  print "read_lammps_rdf"
  rdf_average = lmp_io.read_lammps_rdf("tmp.1.rdf", 3, 1)
  print "read_CG_log_file"
  final_pressure = read_CG_log_file("new_CG.prod1.log")
  print "smooth_data"
  smoothed = dm.smooth_data(rdf_average[1][1])
  print "read_in_rdf_file"
  rdf_array, numofbins, cutoff = read_in_rdf_file("rdf", 3, [[1,1],[1,2],[1,3],[2,2],[2,3],[3,3]])
  print "read_in_interaction_files"
  distance, potential, derivative, pot_file_list, cutoff = lmp_io.read_in_interaction_files("./pot", 3, [[1,1],[1,2],[1,3],[2,2],[2,3],[3,3]], 1)
  #print "lattice: ", lattice
  #print "type_list: ", type_list
  #print "final_pressure: ", final_pressure  
  #print "rdf_average: ", rdf_average[1][1]
  #print "smoothed rdf_average: ", smoothed
  #print len(rdf_average[1][1]), len(smoothed)
  #print "rdf_array: ", rdf_array, "\n numofbins: ", numofbins, "\n cutoff: ", cutoff
  #print "distance: ", distance, "\n potential: ", potential, "\n derivative: ", derivative, "\n pot_file_list: ", pot_file_list, "\n cutoff: ", cutoff
  #print potential[1][1], len(potential[1][1])

if __name__ == "__main__":
  production()
  #basic_test_suite()
