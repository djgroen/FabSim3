# -*- coding: utf-8 -*-
# 
# This source file is part of the FabSim software toolkit, which is distributed under the BSD 3-Clause license. 
# Please refer to LICENSE for detailed information regarding the licensing.
#
# @author: james
# PMF.py is a Python-based implementation of the algorithm which calculates the Potentials of Mean Force.

import os, sys, math
import numpy as np
import scipy 
import pylab
from subprocess import call
import scipy.optimize
from scipy.interpolate import UnivariateSpline
import lib.LammpsIO as lmp_io
import lib.DataAnalysis as da
import lib.DataMorphing as dm
import shutil
# We only need one potential to be optimised, so will use interaction_list_from_file
# This will require the user to supply a file with the potential being optimised.  


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

def read_in_WHAM_file(filename,base_dir='./'):
    """ subroutine to read in the WHAM file - note, the format must be distance is first column, and RDF is the third column 
      ASSUMPTION: ALL WHAM FILES HAVE THE SAME NUMBER OF BINS AND CUTOFF AS THE POTENTIAL FILES. """
    print "reading WHAM %s" % (filename)
    #numofbins, cutoff, o = lmp_io.get_number_of_bins_and_cutoff("%s" % (filename), 0)
    numofbins=0
    # TODO - what if we have a NAN in our data set, due to incomplete sampling?
    LIST_IN = open("%s" % (os.path.join(base_dir,filename)), 'r') 
    index = 0
    x = []
    y = []
    number_of_inf=0
    number_of_non_inf=0

    print numofbins            
    wham_array = [] #np.zeros(numofbins+1)
    wham_array_distance= [] #np.zeros(numofbins+1)
    extrapolate_list=[]
    interpolate_list=[]
    for line in LIST_IN:
        NewRow = (line.strip()).split()
        mystring = NewRow[0][0:1]
        if mystring != "#":
            if len(NewRow)>2:
         
                if NewRow[1] != "inf":
#                    wham_array[index] = float(NewRow[1])
                    number_of_non_inf +=1
                    x.append(float(NewRow[0]))
                    y.append(float(NewRow[1]))
                else:
                    if number_of_non_inf == 0:
                        extrapolate_list.append(index)
                    else:
                        interpolate_list.append(index)
                if number_of_non_inf > 0:
                                   
                    wham_array_distance.append(float(NewRow[0])) 
                    if NewRow[1] == "inf":
                        wham_array.append(0.0)  
                    else :
                        wham_array.append(float(NewRow[1]))
                    index += 1 
    LIST_IN.close()  
    np.asarray(x)
    np.asarray(y)
    np.asarray(wham_array_distance)
    np.asarray(wham_array)
    spl = UnivariateSpline(x, y)
    spl.set_smoothing_factor(0.2)
    for i, distance  in enumerate(wham_array_distance):
        if i in interpolate_list:
            wham_array[i]=float(spl(distance))
            print "WHAM INTER", distance, wham_array[i]
    #print wham_array_distance
    #print wham_array
    np.trim_zeros(wham_array, 'b')
    np.trim_zeros(wham_array_distance, 'b')
    
    last_element=wham_array[index-1]    
    np.subtract(wham_array,last_element)
    # check whether this is the same as the the one in the potential file
    cutoff=wham_array_distance[index-1]
    print wham_array_distance
    print wham_array
    print len(wham_array_distance)
    print len(wham_array)
# need to fill in the infs    
    
    
    return  wham_array, wham_array_distance, len(wham_array_distance), float(cutoff)

def find_dir_value_dict(CG_in_file,base_dir='./'):
    dir_value_dict={}
    dir_spring_const_dict={}
    dir_log_file_dict={}
    dir_data_file_dict={}
    files=os.listdir(base_dir)
    print "FILES", files
    for subdirs in files:
        if os.path.isdir(os.path.join(base_dir,subdirs)):
#            CG_in_file="in.CG.lammps.1"
            full_in_file=os.path.join(*[base_dir,subdirs, CG_in_file])
        
            print "FULL ", full_in_file, CG_in_file 
            if os.path.isfile(full_in_file):
                IN_FILE=open(full_in_file, 'r')             
                for line in IN_FILE:
                    row = line.split()
                    if len(row) > 7 and row[3] == 'spring' and row[4] == 'couple':
                        if 'NULL' in row:
                            constraint_value=float(row[9])
                        else:
                            constraint_value=float(row[10])
                        spring_constant=float(row[6])
                        dir_value_dict[constraint_value]=subdirs
                        dir_spring_const_dict[constraint_value]=spring_constant
                    if len(row) > 0 and row[0] == 'log':
                        log_file=row[1]
                        dir_log_file_dict[constraint_value]=log_file
                    if len(row) > 0 and row[0] == 'read_data':
                        data_file=row[1]
                dir_data_file_dict[constraint_value]=data_file
    print dir_value_dict, "\n"
    print dir_spring_const_dict, "\n"
    print dir_log_file_dict, "\n"
    print "\n"
    return dir_value_dict, dir_spring_const_dict, dir_log_file_dict, dir_data_file_dict

def create_WHAM_files(dir_values_dict, dir_spring_const_dict,dir_log_file,dir_value_dict, wham_list,base_dir_1='./'):
    wham_listings=[]    
    for constraint_values, subdir in dir_values_dict.iteritems():
        base_dir=os.path.abspath(base_dir_1)
        r1_index=0
        success=False
	if base_dir_1.startswith('/net/tesla/srv/home/james/'):
            base_dir_1= base_dir_1[14:]
        print "BASE", base_dir
        CG_log_file=dir_log_file[constraint_values]
        print constraint_values, CG_log_file
        full_log_file=os.path.join(*[base_dir,subdir, CG_log_file])
        if os.path.isfile(full_log_file):
            LOG_FILE=open(full_log_file, 'r')             
       
            WHAM_FILE = open("%s.%.2f" % (os.path.join(base_dir,"wham_file"), float(constraint_values)),'w')               
            for line in LOG_FILE:
                row = line.split()
                if 'r1' in row:
                    ind=row.index("r1")
                    r1_index+=1
                    if r1_index > 1:
                        value=row[ind+2]   
                        success=True
                        WHAM_FILE.write("%d %f\n" % (r1_index-1, float(value)))
            WHAM_FILE.close()
        if success:
            wham_listings.append([float(constraint_values), float(dir_value_dict[constraint_values]),float(2*dir_spring_const_dict[constraint_values])])
            print "APPEND ", float(constraint_values), float(dir_value_dict[constraint_values]),float(2*dir_spring_const_dict[constraint_values])
    wham_listings.sort()
    wham_list_full=os.path.join(base_dir, wham_list)
    WHAM_LIST = open("%s" % (wham_list_full),'w')
    for l in wham_listings:
        print l 
        WHAM_LIST.write("%s/%s.%.2f %f %f \n" % ( base_dir_1, "wham_file", l[0], l[1], l[2]))
    WHAM_LIST.close()

def write_pot_file(filename, distance, derivative, potential, numofbins,  ii, iii, number, smoothing="yes"):

  print "WRITING POT FILE AT:", filename
  OUTPUT_FILE_POT = open (filename, 'w')       
  # outputting the updated potential and forces to a new LAMMPS potential file 
  OUTPUT_FILE_POT.write("# POTENTIAL FOR type %d and type %d\n\nTABLE_%d.%d\nN %d\n\n" % (ii, iii, ii, iii, int(numofbins))) 
  #OUTPUT_FILE_POT.write("# POTENTIAL WITH NAME %s with %d bins.\n\n\n\n\n" % (filename, numofbins))
  index = 0 
  

  if smoothing=="yes":
    #filtered_derivative = dm.smooth_data(np.append(derivative,[0]))
    #workaround to improve smoothing
 #  potential[0] = potential[1]
    filtered_derivative = np.append(derivative,[0])
    filtered_potential  = potential
    if number % 3 ==0:
        filtered_potential  = dm.smooth_data(filtered_potential,window_len=7,window='hamming') #Temporary 
    #filtered_potential  = dm.smooth_data(filtered_potential) 

    # add thresholding to avoid smoothing of charged particles at low distances
    #for i in xrange(0, len(filtered_potential)):
    #  if np.abs(filtered_potential[i]) > 10.0:
    #    blend_factor = np.log(10.0)/np.log(np.abs(filtered_potential[i]))
    #    filtered_potential[i] = filtered_potential[i]*blend_factor + potential[i]*(1.0-blend_factor)
    
  else:
      filtered_potential=potential
      filtered_derivative=derivative
  
  filtered_derivative = da.derivatives(distance, filtered_potential)
  print "LEN DERIVATIVE", len(filtered_derivative), len(filtered_potential), "smoothing: ", smoothing
  last_element=filtered_potential[numofbins-1]
  print "LAST ", last_element
  sub_filtered_potential=np.subtract(filtered_potential,last_element)
  
  for i in xrange(0, numofbins):
    #          if i>340:
    #            print i*DeltaR, derivative[ii][iii][i], len(dy)
  
      OUTPUT_FILE_POT.write("%d\t%f\t%f\t%f   \n" % (i+1, distance[i], sub_filtered_potential[i], filtered_derivative[i]*-1))
  
  
  OUTPUT_FILE_POT.close()


def update_one_file_wham(number, numofbins, new_distance_wham, new_wham, correct_distance_wham, correct_wham, previous_distance, previous_potential,atom1,atom2,dir_value_dict,pot_file_new,CG_in_file_base,out_path,base_dir='./'):
  
  number = int(number)
  potential = np.zeros((numofbins+1)) 
  derivative = np.zeros((numofbins+1))
  new_number = number + 1 

# TODO - check the relationships between correct WHAM distances and the potential file 
  index = length = 0 
  x_data = []
  y_data = []
  success = False
  extrapolate_list=[]
  kB = 0.0019858775
  
  error=0.0
  index_error=0
  mapping_array=np.searchsorted(previous_distance,new_distance_wham)
  mapping_array_whams=np.searchsorted(correct_distance_wham,new_distance_wham)
  a=mapping_array.tolist()
  b=mapping_array_whams.tolist()
  print mapping_array
  print mapping_array_whams
  print numofbins
  for i in xrange(0, numofbins+1): 
      print i 
      if i in a:
          
          ind=a.index(i)
          print ind          
          ind2=b[ind]
          diff=correct_wham[ind2] - new_wham[ind]
          print new_wham[ind], correct_wham[ind2], previous_distance[i], previous_potential[i]
          print "DIFF ", ind, new_wham[ind], ind2, correct_wham[ind2], previous_distance[i], previous_potential[i]
#        print old_distance[1], i, i*DeltaR
      
          potential[i] = previous_potential[i] + diff
          if (math.exp(-1*abs(correct_wham[ind2])/(kB*300)) > 1E-9):
              error+=diff*diff
              index_error+=1
              print "ERROR index", index_error, previous_distance[i], correct_wham[ind2], error, math.exp(-1*abs(correct_wham[ind2])/(kB*300))
          y_data.append(float(potential[i]))
          x_data.append(float(previous_distance[i]))

      else:
        # this array indicates which values we need to an extrapolation for the potential and for the forces (negative of the potential derivative) - defined as where 
        # the RDF is less than 0.15, yet is defined in the old potential file. 
        extrapolate_list.append(i) 
  final_error=error/index_error
  print "ERROR is ", final_error, math.sqrt(final_error)
  #exit()    
  h=np.asarray(x_data)
  l=np.asarray(y_data)  
  
  dy = da.derivatives(h, l) 
    
#      print y_data, dy, len(y_data), len(dy)
#      exit()
    
  parameters = {} 
  square_residual = 0 

    # fitting the potential derivative (i.e. negative forces) using CurveFit.pm to a Lennard Jones 6 - 3 potential (i.e. 7 - 4 when differentiated )       
  fitfunc = lambda p, x: - 6 * (( ( 4 * p[0] * p[1]**6) / x**7) - ( (4 * p[0] * p[1]**3) / (2*x**4)) )
  errfunc = lambda p, x, y: fitfunc(p, x) - y
    #print "X_DATA = ", x_data, dy, y_data

  p0 = np.array([0.5, 4.5]) #was 0.5,4.5
  p1, success = scipy.optimize.leastsq(errfunc, p0[:], maxfev=5000, args=(h, dy))  #use [:int(4.0/DeltaR)] to optimize up to a cutoff of 4.
    
  if success == 0:
      print "Scipy.optimize did not manage to converge the fit on dataset", "! Exiting now."
      exit()

  LJ_OUT = open("LJ_parameters",'w') 
  LJ_OUT.write("LJ PARAMETERS %d %d p0 = %f, p1 = %f\n" % (atom1, atom2, p1[0], p1[1]))      
  LJ_OUT.close()

  for i in xrange(numofbins+1, 0, -1):
      if i in extrapolate_list: #77-31
        #print i
    
            new_distance = previous_distance[i]
          # These Lennard-Jones forces are then numerically integrated to get the potential
            derivative[i] = -np.abs(fitfunc(p1, new_distance))
            diff = x_data[0] - new_distance
            ave = 0.5 * fitfunc(p1, new_distance) - 0.5 * dy[0]
            r_y = np.abs(y_data[0] - diff * ave)
            potential[i] = r_y
            print i, derivative[i], potential[i], "!"
     
            
  a=np.delete(previous_distance,0)
  b=np.delete(potential,0)
  
  derivatives = da.derivatives(a, b) 
#    index = 0
  for i in xrange(numofbins):
#      if i not in conversion_extrapolate_tmp.keys():
      print i, a[i], b[i], derivatives[i]
  for constraint_values, subdir in dir_value_dict.iteritems():
      CG_in_file= CG_in_file_base #+ str(number)
      new_CG_in_file= CG_in_file_base #+ str(new_number)
      full_in_file=os.path.join(*[base_dir,subdir, CG_in_file])
     
      full_out_file=os.path.join(*[out_path,subdir, new_CG_in_file])
      print "FULL OUT", full_out_file
      new_dir=os.path.dirname(full_out_file)
      if not os.path.exists(new_dir):
        os.makedirs(new_dir)
      pot_file_relative = os.path.split(pot_file_new)
      relative_pot_file= '../' + str(pot_file_relative[1])
      if os.path.isfile(full_in_file):
          IN_FILE=open(full_in_file, 'r')  
          OUT_FILE=open(full_out_file, 'w+')
          for line in IN_FILE:
                row = (line.strip()).split()
                if len(row) > 0:
                    print row
                    if row[0] == "pair_coeff":
                        if (row[1] == str(atom1) and row[2] == str(atom2)) or (row[1] == atom2 and row[2] == atom1 ):
                            OUT_FILE.write("pair_coeff %d %d %s TABLE_%d.%d \n" % (atom1, atom2,relative_pot_file,atom1,atom2)) 
                        else:
                            OUT_FILE.write("%s\n" % (line.strip()))
                    
                    else:
                        OUT_FILE.write("%s\n" % (line.strip()))
                    if row[0] == "read_data":
                        full_lammps_datafile=os.path.join(*[base_dir,subdir, str(row[1])])
                        full_new_lammps_datafile=os.path.join(*[out_path,subdir, str(row[1])])
                        shutil.copy2(full_lammps_datafile, full_new_lammps_datafile)
                            
#        derivative[i] = dy[index]
#        index += 1 
#    
#    index = 0
#    for i in xrange(0, numofbins+1):
#      if len(derivative) > i:
#        if abs(derivative[i]) > 0:
#          index += 1 
#          # determining the number of potential values
  write_pot_file(pot_file_new, a,  derivatives, b, numofbins, atom1, atom2,number)  
#  write_pot_file(pot_file_new, previous_distance,  derivative, potential, numofbins, atom1, atom2,number) 
    #first index was numofbins
def production():

    print "ARGUMENTS to the PMF calculation are: ", sys.argv
    wham_correct_file = ""
    number=""
    atom_type1=""
    atom_type2=""
    out_path=""
    CG_in_file_base=""
    pot_base=""
    wham_executable=""
    lammps_input_file = ""
    
    number_of_arguments = len(sys.argv) 
    for i in xrange(0, number_of_arguments):  
        if sys.argv[i].lower() == "wham_correct_file":
            wham_correct_file = sys.argv[i+1] 
            print "THE WHAM CORRECT FILE IS ", wham_correct_file 
        elif ((sys.argv[i] == "potential_base") or (sys.argv[i] == "potential") or (sys.argv[i] == "pot_base")):
             pot_base_full = os.path.split(sys.argv[i+1])
             pot_base_file = pot_base_full[1] 
             pot_base_dir=pot_base_full[0]
             pot_base=sys.argv[i+1]
        elif ((sys.argv[i].lower() == "atom_type1") or (sys.argv[i].lower() == "atom1") or (sys.argv[i].lower() == "type1")):
            atom_type1 = int(sys.argv[i+1]) 
        elif ((sys.argv[i].lower() == "atom_type2") or (sys.argv[i].lower() == "atom2") or (sys.argv[i].lower() == "type2")):
            atom_type2 = int(sys.argv[i+1]) 
        elif ((sys.argv[i] == "number") or (sys.argv[i] == "current_number") or (sys.argv[i] == "iteration_number")):
            number = int(sys.argv[i+1])
            print "THE CURRENT ITERATION NUMBER IS ", number
        elif ((sys.argv[i] == "CG_in_file") or (sys.argv[i] == "CG_lammps_file") or (sys.argv[i] == "CG_input")):
            
            CG_in_file = sys.argv[i+1]
        elif ((sys.argv[i].lower() == "lammps_in_file") or (sys.argv[i] == "lammps_input_file") or (sys.argv[i] == "lammps_input")):
            lammps_input_file_full=os.path.split(sys.argv[i+1])
            lammps_input_file = lammps_input_file_full[1]
            lammps_input_file_dir=lammps_input_file_full[0]
            lammps_input_file_full=sys.argv[i+1]
        elif ((sys.argv[i] == "wham_executable") or (sys.argv[i] == "wham_executable_path") or (sys.argv[i] == "wham_path")):
            wham_executable = sys.argv[i+1]
        elif ((sys.argv[i] == "out_directory") or (sys.argv[i] == "out")):
            out_path = sys.argv[i+1]
            if not os.path.isdir(out_path):
                os.makedirs(out_path)
        
                
#wham_correct_file=sys.argv[1]
#number=sys.argv[2]
#atom_type_1=int(sys.argv[3])
#atom_type_2=int(sys.argv[4])
#out_path=sys.argv[5]
#CG_in_file_base="in.CG.lammps.1"
    wham_array_correct, wham_array_distance_correct, numofbins_wham, cutoff_wham= read_in_WHAM_file(wham_correct_file)
    dir_value_dict, dir_spring_const_dict, dir_log_file_dict, dir_data_file_dict =find_dir_value_dict(CG_in_file,lammps_input_file_dir)
    print "LAMMPS input_dir", lammps_input_file_dir
    wham_spacing=wham_array_distance_correct[1]-wham_array_distance_correct[0]
    wham_minimum=wham_array_distance_correct[0]-(wham_spacing/2)
    wham_maximum=wham_array_distance_correct[numofbins_wham-1]+(wham_spacing/2)
    wham_list_base="wham_list_CG"
    wham_list=os.path.join(lammps_input_file_dir, str(wham_list_base + '.' + str(number)))
    wham_output=os.path.join(lammps_input_file_dir, str("wham_output"+ '.' + str(number)))
    print "WHAMLIST", wham_list, wham_output
    pot_file=pot_base + str(number)
    new_number=int(number)+1
    print "NEW NUMBER", new_number, number
    pot_new=pot_base_file+str(new_number)
    pot_file_new=os.path.join(out_path,pot_new)
    print "POT_FILE NEW", pot_file_new, out_path
    print "NUMOFBINS IS ", numofbins_wham
    create_WHAM_files(dir_value_dict, dir_spring_const_dict,dir_log_file_dict,dir_value_dict,wham_list,lammps_input_file_dir)
    print "WHAM", wham_list, wham_output
    call("'%s' '%f' '%f' '%d' 0.0001 500 0 '%s' '%s' " % (wham_executable, wham_minimum, wham_maximum, numofbins_wham, wham_list, wham_output), shell=True)
#2.875  20.125 69 0.0001 500 0  wham_list_CG.number wham_output.number')
    wham_array_new, wham_array_distance_new, numofbins_new, cutoff_wham_new= read_in_WHAM_file(wham_output,lammps_input_file_dir)
    num_of_pot_bins, cutoff_pot, offset_pot = lmp_io.get_number_of_bins_and_cutoff(pot_file,0)
    pot_distance, pot_potential, pot_derivative=lmp_io.read_in_interaction_file(pot_file,num_of_pot_bins)

    update_one_file_wham(number, num_of_pot_bins, wham_array_distance_new, wham_array_new, wham_array_distance_correct, wham_array_correct, pot_distance, pot_potential,atom_type1,atom_type2,dir_value_dict,pot_file_new,CG_in_file,out_path,lammps_input_file_dir)
    new_lammps_input_file=os.path.join(out_path,lammps_input_file)
    shutil.copy2(lammps_input_file_full, new_lammps_input_file)
if __name__ == "__main__":
  production()
