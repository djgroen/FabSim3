import os, sys, math
import numpy as np
import scipy 
import pylab
import scipy.optimize
import lib.LammpsIO as lmp_io
import lib.DataMorphing as dm
import lib.DataAnalysis as da
import argparse

if __name__ == "__main__":

  parser = argparse.ArgumentParser(description='Modify a potential.')
  parser.add_argument("-i", "--inputfile", help='name of the potential file to read')
  parser.add_argument("-m", "--mode", default='smooth', help='type of filter used', choices=["smooth", "remove_tail", "append_zeroes", "amplify", "xshift", "yshift", "prepend", "append_linear"])
  parser.add_argument("-r", "--repeat", help='number of repetitions', type=int, default=1)
  parser.add_argument("-a", "--atom1", help='atom number 1', type=int, default=1)
  parser.add_argument("-b", "--atom2", help='atom number 2', type=int, default=1)
  parser.add_argument("-o", "--outputfile", help='name of the potential file to write')
  parser.add_argument("parameter", type=float, help='specifies a key parameter to associate with the mode. Should be at least 1e-10.', default=0.0)
  

  args = parser.parse_args()
  print args

  num_of_bins, cutoff, offset = lmp_io.get_number_of_bins_and_cutoff(args.inputfile, 1)
  print "Potential numofbins and cutoff:", num_of_bins, cutoff

  dis, pot, der = lmp_io.read_in_interaction_file(args.inputfile, num_of_bins)
  dis = dis[1:]
  pot = pot[1:]
  der = der[1:]
  
  for i in xrange(0,args.repeat):
    if args.mode == "smooth":
      pot = dm.smooth_data(pot,window_len=int(args.parameter),window='flat')
    elif args.mode == "remove_tail":
      pot, der = dm.remove_tail(pot, der)
    elif args.mode == "append_zeroes":
      if abs(args.parameter) < 1e-10:
        args.parameter = 20
      dis, pot, der = dm.append_zeroes(dis, pot, der, args.parameter) #we prefer this to be 20
    elif args.mode == "amplify":
      if args.parameter < 1e-10:
        args.parameter = 1
      pot *= args.parameter
    elif args.mode == "xshift":
      dis -= args.parameter
      if args.parameter < 0:
        dis, pot, der = dm.append_zeroes(dis, pot, der, cutoff + args.parameter)
    elif args.mode == "yshift":
      pot += args.parameter
    elif args.mode == "prepend":
      dis, pot, der = dm.prepend_linear(dis,pot,der,args.parameter)
    elif args.mode == "append_linear":
      dis, pot, der = dm.append_linear(dis,pot,der,args.parameter)

#    elif args.mode == "section_raise_weighted":
#    elif args.mode == "section_raise_gauss":

  if args.mode is not ("prepend" or "append_linear"):
    der = da.derivatives(dis, -pot)
  
  print "Distance starts at: ", dis[0], dis[1]
  
  lmp_io.write_pot_file(args.outputfile, -der, pot, len(dis), dis[1]-dis[0], int(args.atom1), int(args.atom2), num_of_bins, offset=dis[0], smoothing="no",
selection="no") 
