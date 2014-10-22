import numpy as np
import os.path
import DataMorphing as dm
import DataAnalysis as da

def load_target_and_cg_rdf(target_filename, cg_filename, averaging='yes'):
  """ Loads two preprocessed rdf files (named rdf_* for the CG ones, and rdf.* for the target ones) and 
  provides difference and squared difference values. """

  print "loading rdfs: ", target_filename, cg_filename
  
  d1 = np.loadtxt(target_filename)
  d2 = np.loadtxt(cg_filename)
  
  if (len(d2) < len(d1)):
    d3 = d2[:,1] - d1[:len(d2)-len(d1),2]
    d4 = np.power(d2[:,1] - d1[:len(d2)-len(d1),2], 2)
  elif (len(d2) > len(d1)): 
    d3 = d2[:len(d1)-len(d2),1] - d1[:,2]
    d4 = np.power(d2[:len(d1)-len(d2),1] - d1[:,2], 2)
  else: 
    d3 = d2[:,1] - d1[:,2] 
    d4 = np.power(d2[:,1] - d1[:,2], 2)
      
  if averaging == 'yes':    
    d3 = np.average(np.absolute(d3))
    d4 = np.average(d4)
    
  return d1, d2, d3, d4

def grow_dict_array(arrays_dict, arraylabel, new_elem):
  """Dicts with elements containing np arrays are common here. This is a method to easily append elements to the
  arrays, initializing a new array with the requisite arraylabel when there is none."""  
  if arraylabel in arrays_dict.keys():
    arrays_dict[arraylabel] = np.append(arrays_dict[arraylabel], new_elem) 
  else:
    arrays_dict[arraylabel] = np.array([new_elem])

#def load_atoms_from_file(lammps_pos_file, max_num_atoms):
#  LIST_IN = open(lammps_pos_file, 'r')
#  for line in LIST_IN:
#    NewRow = (line.strip()).split()

def get_number_of_bins_and_cutoff(filename, cutoff_col_index):
  """ Find number of bins in a file. """
  LIST_IN = open(filename, 'r') 
  number_of_bins = 0
  cutoff = 0
  offset = 0
  for line in LIST_IN:
    if line[0:1] != "#":
      NewRow = (line.strip()).split()
      if len(NewRow)>2:
        if number_of_bins == 0:
          offset = float(NewRow[cutoff_col_index])
        number_of_bins += 1
        cutoff = float(NewRow[cutoff_col_index])
  LIST_IN.close()
  
  return number_of_bins, cutoff, offset

def get_number_of_types(source_rdf_file):
  """ read a tmp.*.rdf file and obtain the number of particle types in the system. """
  index = 0
  LIST_IN = open(source_rdf_file, 'r')
  for line in LIST_IN:
    NewRow = (line.strip()).split()
    if NewRow[0] == "1":
      num_interactions = (len(NewRow)-2)/2
      num_types = 1
      while num_interactions > num_types*(num_types-1)/2 + num_types:
        num_types += 1
      print "num_types = ", num_types
      return num_types
    
  
def get_max_number_of_bins(filename, interaction_list, cutoff_col_index):
  """ Invoke get_number_of_bins and get the max num_of_bins"""
  max_num_of_bins = max_cutoff = 0
  for i in interaction_list:
    n, c, o = get_number_of_bins_and_cutoff("%s.%d.%d" % (filename, i[0], i[1]), cutoff_col_index)
    if n > max_num_of_bins:
      max_num_of_bins = n
    if c > max_cutoff:
      max_cutoff = c
  return max_num_of_bins, max_cutoff

def read_pot_file(filename):
  return np.loadtxt(filename, skiprows=5)
  
def read_in_interaction_file(filename, number_of_bins):
  """ subroutine to read in a single LAMMPS formatted interaction potential"""
  distance = np.zeros((number_of_bins+1))
  potential = np.zeros((number_of_bins+1)) 
  derivative = np.zeros((number_of_bins+1)) 
  print "OPENING FILE %s" % (filename) 
  LIST_IN = open(filename, 'r') 
     
  element_count = 0 # element_count is a surrogate for the numbering of the
  # elements (int(NewRow[0])). 
  # The original numbering may be inconsistent in the source file. We do not
  # want that to
  # propagate to new files...
  
  for line in LIST_IN:
    if line[0:1] != "#":
      NewRow = (line.strip()).split() 
      if len(NewRow)>3:
        element_count += 1
        if abs(float(NewRow[3])) > 0:
          distance[element_count]   = float(NewRow[1])
          potential[element_count]  = float(NewRow[2])
          derivative[element_count] = float(NewRow[3])             
  return distance, potential, derivative

def read_in_interaction_files(filename, num_of_types, interaction_list, number):
  """ subroutine to read in the LAMMPS formatted interaction potentials """
  print filename
  number_of_bins, cutoff = get_max_number_of_bins(filename, interaction_list, 1) 
  # ...Does a full sweep instead of header parsing, slower, more robust. Slightly overshoots for LAMMPS files with many parameters.
  distance = np.zeros((num_of_types+1, num_of_types+1, number_of_bins+1))
  potential = np.zeros((num_of_types+1, num_of_types+1, number_of_bins+1)) 
  derivative = np.zeros((num_of_types+1, num_of_types+1, number_of_bins+1)) 
  pot_file_list = [] 
    
  for i in interaction_list:
    if number == 1:
      pot_file_list.append("%s.%d.%d" % (filename, i[0], i[1]))
    else:
      old_number = int(number)
      pot_file_list.append("%s.%d.%d" % (filename, i[0], i[1]))
    distance[i[0]][i[1]], potential[i[0]][i[1]], derivative[i[0]][i[1]] = read_in_interaction_file(pot_file_list[-1], number_of_bins)

  return distance, potential, derivative, pot_file_list, cutoff
  
  

def load_quantity_from_file(lammps_log_file, quantity, row_offset=0):
  """Load a LAMMPS pressure file and return arrays with the time steps and pressure values."""
  #print "LQFF:", quantity
  steps = []
  pressures = []
  LIST_IN = open(lammps_log_file, 'r')
  for line in LIST_IN:
    NewRow = (line.strip()).split()
    if len(NewRow) > row_offset:
      if NewRow[row_offset] == quantity:
        pressures.append(float(NewRow[2]))
      elif NewRow[0] == "Step":
        steps.append(int(NewRow[2]))
  return np.array(steps[5:]), np.array(pressures[5:])

def load_pressure_from_file(lammps_log_file):
  return load_quantity_from_file(lammps_log_file,"Press")

def read_lammps_rdf(lammps_rdf_file, number_of_types, ibi_iteration_number, timestep_limit=0, write_rdf_files=True, timestep_threshold=20): 
  """ subroutine to read in the rdf outputted by LAMMPS. This needs to be averaged - it is a collection of snapshot RDFS 
  at a regular frequency. We ignore the first nineteen results (start at 20). Note the RDF starts on line 6 of the files, 
  and includes a header of two lines before each snapshot RDF. """

  print "Reading: ", lammps_rdf_file
  #print "number_of_types", number_of_types

  number_of_types += 1
  index = index2 = 0 
  timestep = 0 
  number_of_bins = number_of_rdfs = 0 
  deltaR = 0
  rdf_sum = np.zeros((1,1))
  first_value = 0
  rowrange = []
  
  #read data from lammps file
  LIST_IN = open(lammps_rdf_file, 'r')
  for line in LIST_IN:
    NewRow = (line.strip()).split()
    index += 1 

    if number_of_bins > 0:
      index2 += 1
    if index < 8:
      if index == 4:
        number_of_bins = int(NewRow[1]) 
        print "Number of bins is:", number_of_bins
        rdf_sum = np.zeros((number_of_types*number_of_types*2, number_of_bins+1))
      elif index == 6:
        first_value = float(NewRow[1])
        deltaR = float(NewRow[1])
        number_of_rdfs = len(NewRow) - 2     
        rowrange = range(2, len(NewRow))
      elif index == 7:
        deltaR = float(NewRow[1]) - first_value    
    if (index > 5 and len(NewRow) > 3):
      if (timestep > timestep_threshold):
        for n in rowrange:
          rdf_sum[n-2][int(NewRow[0])] += float(NewRow[n])  
    elif (index2 % (number_of_bins + 1) == 0 and index2 > 0):
      timestep += 1
      if timestep_limit > 0 and int(NewRow[0]) > timestep_limit: #timestep limiter. Useful for partial rdf analysis
        break;
      # print "TIMESTEP is $NewRow[0] $number_of_rdfs \n"
  LIST_IN.close()
  
  print "read completed."
  
  rdf_average = np.zeros((number_of_types, number_of_types, number_of_bins+1))
  rdf_column = 0  
  timestep -= timestep_threshold # subtract the 19 in advance to speed things up a little.
  for type_number in xrange(1, number_of_types):
    for type_number2 in xrange(type_number, number_of_types):
      rdf_average[type_number][type_number2] = rdf_sum[rdf_column] / timestep       
      if write_rdf_files:
        print "WRITING RDF_ FILE AT: %s/rdf_%d.%d.%d" % (os.path.dirname(lammps_rdf_file), int(ibi_iteration_number),type_number,type_number2)
        OUTPUT_FILE_RDF = open("%s/rdf_%d.%d.%d" % (os.path.dirname(lammps_rdf_file), int(ibi_iteration_number),type_number,type_number2), 'w')
        for n in xrange(1, number_of_bins+1):
          OUTPUT_FILE_RDF.write("%f %f\n" % ((n-1)*deltaR, rdf_average[type_number][type_number2][n])) 
        OUTPUT_FILE_RDF.close()
      rdf_column += 2
      
  return rdf_average 
  

def read_lammps_data_file(lammps_data):
  """Reads in a lammps data file - returns the number of each CG type and the lattice constants (arrays)."""
  switch  = "none"
  type_list = {} # number of each CG type 
  lattice = np.zeros((3)) # lattice constants

  #read data from lammps file
  LIST_IN = open(lammps_data, 'r')
  print "Starting to read: ", lammps_data
  
  for line in LIST_IN:
    NewRow = (line.strip()).split()
    if len(NewRow)>0:     
      NewRow[0] = NewRow[0].lower() # enable case-insensitive string compares.    
      if NewRow[0] == "bonds":
        switch = "bonds"
      if switch == "atoms":
        if len(NewRow)>6:
          #print NewRow[2], NewRow[0]
          grow_dict_array(type_list, NewRow[2], NewRow[0])
      if NewRow[0] == "atoms":
        switch = "atoms"
      if len(NewRow)>2:
        if NewRow[2] == "xlo":
          lattice[0] = float(NewRow[1]) - float(NewRow[0])
        if NewRow[2] == "ylo":
          lattice[1] = float(NewRow[1]) - float(NewRow[0])
        if NewRow[2] == "zlo":
          lattice[2] = float(NewRow[1]) - float(NewRow[0])

  LIST_IN.close()
  return lattice, type_list 

  
def write_pot_file(filename, derivative, potential, numofbins, DeltaR, ii, iii, index, offset=0, smoothing="yes", selection="yes"):

  print "WRITING POT FILE AT:", filename
  OUTPUT_FILE_POT = open (filename, 'w')       
  # outputting the updated potential and forces to a new LAMMPS potential file 
  OUTPUT_FILE_POT.write("# POTENTIAL FOR type %d and type %d\n\nTABLE_%d.%d\nN %d\n\n" % (ii, iii, ii, iii, index)) 
  #OUTPUT_FILE_POT.write("# POTENTIAL WITH NAME %s with %d bins.\n\n\n\n\n" % (filename, numofbins))
  index = 0 
  
  filtered_derivative = np.append(derivative,[0])
  filtered_potential  = potential
  if smoothing=="yes":
    #filtered_derivative = dm.smooth_data(np.append(derivative,[0]))
    #workaround to improve smoothing
    potential[0] = potential[1]
    #filtered_potential  = dm.smooth_data(filtered_potential,window_len=7,window='hamming') #Temporary 
    filtered_potential  = dm.smooth_data(filtered_potential) 

    # add thresholding to avoid smoothing of charged particles at low distances
    #for i in xrange(0, len(filtered_potential)):
    #  if np.abs(filtered_potential[i]) > 10.0:
    #    blend_factor = np.log(10.0)/np.log(np.abs(filtered_potential[i]))
    #    filtered_potential[i] = filtered_potential[i]*blend_factor + potential[i]*(1.0-blend_factor)
    filtered_derivative = da.derivatives(np.arange(offset, offset+(numofbins+1)*DeltaR, DeltaR),filtered_potential)
 
  print "LEN DERIVATIVE", len(filtered_derivative), len(filtered_potential), "smoothing: ", smoothing
  
  for i in xrange(0, numofbins+1):
    #          if i>340:
    #            print i*DeltaR, derivative[ii][iii][i], len(dy)
    if selection=="yes" and len(derivative) > i:
      if abs(derivative[i]) > 0:
        #              print i, index, i*DeltaR, len(derivative[ii][iii]), numofbins, len(filtered_potential), len(filtered_derivative)
        index += 1
        OUTPUT_FILE_POT.write("%d\t%f\t%f\t%f   \n" % (index, i*DeltaR+offset, filtered_potential[i], filtered_derivative[i]*-1))
    if selection=="no" and i < numofbins:
      index += 1
      OUTPUT_FILE_POT.write("%d\t%f\t%f\t%f   \n" % (index, i*DeltaR+offset, filtered_potential[i], filtered_derivative[i]*-1))
  
  OUTPUT_FILE_POT.close()
