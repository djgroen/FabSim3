# 
# This source file is part of the FabSim software toolkit, which is distributed under the BSD 3-Clause license. 
# Please refer to LICENSE for detailed information regarding the licensing.
#
# This file contains routines which are used to reduce simulation data produced by LAMMPS.

import os, sys, math
import numpy as np
import scipy
import pylab
#import lib.LammpsIO as lmp_io
import mpl_toolkits.mplot3d.axes3d as p3

# This file contains a large set of simple routines, intended to analyze data coming from clay-polymer simulations.
# Some of this functionality is more general-purpose, and should be brought to a different file.


def get_clay_sheets_from_pos_file(fname):
  fp  = open(fname, 'r')
  
  sheets = np.zeros((1,4))
  
  c=0
  for line in fp:
    NewRow = (line.strip()).split() 
    if int(NewRow[1]) > 2:
      sheets = np.append(sheets,np.array([[NewRow[1], NewRow[2], NewRow[3], NewRow[4]]]))
      c += 1
      print "sheet_particle count: ", c
      
  return sheets

def split_pos_file(fname):
  fp  = open(fname, 'r')
  fname2 = os.path.basename(fname)
  outputs = [0, open("%s.1" % fname2, 'w'), open("%s.2" % fname2, 'w'), open("%s.3" % fname2, 'w'), open("%s.4" % fname2, 'w')]
 
  for line in fp:
    NewRow = (line.strip()).split()
    if len(NewRow)>1:
      outputs[int(NewRow[1])].write(line) 
  return ["%s.1" % fname2, "%s.2" % fname2, "%s.3" % fname2, "%s.4" % fname2] 

def file_len(fname):
  i = 0
  with open(fname) as f:
    for i, l in enumerate(f):
      pass
  return i + 1      
      
def pos2xyz(fname, xyz_name, total_particle_count):     
  fpin  = open(fname, 'r')
  fpout = open(xyz_name, 'w')
  fpout.write("%s\n" % file_len(fname))
  fpout.write("xyz from %s\n" % fname)
  
  if total_particle_count == 14726656: 
    vol = [1609.59, 1611.11, 960.838] #pva8
  else:
    vol = [402.398, 402.778, 240.21] # pva2
  
  for line in fpin:
    NewRow = (line.strip()).split()
    fpout.write("O %s %s %s\n" % (vol[0]*float(NewRow[2]), vol[1]*float(NewRow[3]), vol[2]*float(NewRow[4])))


def get_molecule_from_input(input_fname, molecule_number, atom_row_length=8): #set atom_row_length=10 if you're reading coords from a RESTART file, or atom_row_length=8 if from a POS file (or 2 if an INDEX file).
  fp  = open(input_fname, 'r')
  molecule = []
  for line in fp:
    NewRow = (line.strip()).split()
    if len(NewRow) == atom_row_length:
      if int(NewRow[1]) == molecule_number:
        molecule.append(line.strip())
#        print line.strip()
  return molecule

def get_molecule_particles_from_indexfile(input_fname, molecule_number):
  fp  = open(input_fname, 'r')
  molecule = []
  for line in fp:
    NewRow = (line.strip()).split()
    if len(NewRow) == 2:
      if int(NewRow[1]) == molecule_number:
        molecule.append(int(NewRow[0]))
#        print line.strip()
  return molecule


#TODO: Write!
#def get_lattice_dimensions_from_restart_file():

def get_particle_coordinates_from_pos_file(pos_fname, particle_list, xyz_boundaries = np.array([402.398, 402.778, 240.21]), atom_row_length=8, coordinate_offset=0):
  fp  = open(pos_fname, 'r')
  particles = np.array([0.0, 0.0, 0.0])

  min_part_num = np.min(particle_list)
  max_part_num = np.max(particle_list)

  for line in fp:
    NewRow = (line.strip()).split()
    if len(NewRow) == atom_row_length:
      part_num_read = int(NewRow[0])
      if part_num_read >= min_part_num:
        if part_num_read <= max_part_num:
          if part_num_read in particle_list:
            particles = np.vstack((particles, np.array([float(NewRow[coordinate_offset+2])*xyz_boundaries[0], float(NewRow[coordinate_offset+3])*xyz_boundaries[1], float(NewRow[coordinate_offset+4])*xyz_boundaries[2]]) ))
    
  return particles[1:]

def get_coords_from_line(line, offset=0): #set offset=2 if you're reading coords from a RESTART file, or offset=0 if from a POS file.
  ii = (line.strip()).split()
  return np.array([float(ii[offset+2]), float(ii[offset+3]), float(ii[offset+4])])

def get_coords_from_lines(lines):
  result = np.array([0.0, 0.0, 0.0])
  for l in lines:
    result = np.vstack((result, get_coords_from_line(l)))
  return result 
 
def calc_dist_with_periodics(a, b, bounds):
  min_dists = np.min(np.dstack(((a - b) % bounds, (b - a) % bounds)), axis = 2)
  dists = np.sqrt(np.sum(min_dists ** 2, axis = 1))
  return dists

def calc_min_dist_with_periodics(a, b, bounds):
  min_dist = 1.0e10
  for i in a:
    tmp_dists_local = np.min(np.dstack(((i - b) % bounds, (b - i) % bounds)), axis = 2)
    dists_local =  np.sum(tmp_dists_local ** 2, axis = 1)
    min_dist_local = np.min(dists_local)
    min_dist = min(min_dist, np.sqrt(min_dist_local))

  return min_dist




def calc_distance_between_molecules(m1, m2, xyz_boundaries = np.array([402.398, 402.778, 240.21]), raw_particle_data="no"):
  mindist = 1.0e8
  xyz_1 = m1
  xyz_2 = m2
  if raw_particle_data == "yes":
    xyz_1 = get_coords_from_lines(m1)    
    xyz_2 = get_coords_from_lines(m2)

  return calc_min_dist_with_periodics(xyz_1, xyz_2, xyz_boundaries)

def write_particle_molecule_index_list(input_fname, molecule_number_list, exclude_mode='no'):

  fp  = open(input_fname, 'r')
  molecule = []
  if exclude_mode == 'no':
    for line in fp:
      NewRow = (line.strip()).split()
      if len(NewRow) == 8:
        if int(NewRow[1]) in molecule_number_list:
          print NewRow[0], NewRow[1]
  else:
    for line in fp:
      NewRow = (line.strip()).split()
      if len(NewRow) == 8:
        if int(NewRow[1]) not in molecule_number_list:
          print NewRow[0], NewRow[1]
  
