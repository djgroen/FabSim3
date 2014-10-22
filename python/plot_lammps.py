import os, sys, math
import numpy as np
import scipy 
import pylab
import lib.LammpsIO as lmp_io
import mpl_toolkits.mplot3d.axes3d as p3

def smooth_data(x,window_len=13,window='flat'):
  """smooth the data using a window with requested size. courtesy of the scipy cookbook.
  This method is based on the convolution of a scaled window with the signal.
  The signal is prepared by introducing reflected copies of the signal 
  (with the window size) in both ends so that transient parts are minimized
  in the begining and end part of the output signal. Output length equals input length here
  """
  if x.ndim != 1:
    raise ValueError, "smooth only accepts 1 dimension arrays."
  if x.size < window_len:
    raise ValueError, "Input vector needs to be bigger than window size."
  if window_len<3:
    return x   
  if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
    raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"   
  s=np.r_[x[window_len-1:0:-1],x,x[-1:-window_len:-1]]
  if window == 'flat': #moving average
    w=np.ones(window_len,'d')
  else:
    w=eval('np.'+window+'(window_len)')      
  y=np.convolve(w/w.sum(),s,mode='valid')
      
  return y[(window_len/2):-(window_len/2)]

def set_small_legend():
  l = pylab.legend(loc=4)
  l.get_title().set_fontsize('8') 
  pylab.plt.setp(pylab.gca().get_legend().get_texts(), fontsize='8')

def add_one_potential_plot(filename, row, column, index, fig):
  d1 = np.loadtxt(filename, skiprows=5)
  ax = fig.add_subplot(row,column,index)

  pylab.ylim([-0.35,0.35])
  pylab.xlim([0,20])
  
  ax.plot(d1[:,1],d1[:,2], label="potential: %s" % filename)
  ax.plot(d1[:,1],np.zeros(( len(d1[:,1]) )))

  set_small_legend()

def add_potential_plot(iter, molecule1, molecule2, row, column, index, fig):
  d1 = np.loadtxt("pot.%d.new.%d.%d" % (iter, molecule1, molecule2), skiprows=5)
  print "READ: pot.%d.new.%d.%d" % (iter, molecule1, molecule2)
  if iter > 1:
    d2 = np.loadtxt("pot.%d.new.%d.%d" % (iter-1, molecule1, molecule2), skiprows=5)
    print "READ: pot.%d.new.%d.%d" % (iter-1, molecule1, molecule2)
  
  ax = fig.add_subplot(row,column,index)
     
  ax.plot(d1[:,1],d1[:,2], label="current iteration %d %d" % (molecule1, molecule2))
  ax.plot(d1[:,1],np.zeros(( len(d1[:,1]) )))
  if iter > 1:
    ax.plot(d2[:,1],d2[:,2], label='last iteration')
      
  pylab.legend(loc=4)
      
  pylab.ylim([-0.35,0.35])  
  pylab.xlim([0,20]) 
  
  set_small_legend()

def txt_rdf(iter, molecule1, molecule2):
  if molecule2 > 0:
    d1, d2, d3, d4 = lmp_io.load_target_and_cg_rdf("rdf.%d.%d" % (molecule1, molecule2), "rdf_%d.%d.%d" % (iter-1, molecule1, molecule2))
    print iter, " for particles ", molecule1, molecule2, "ave. diff: %f, quad. diff: %f" % (d3, d4)
  else:
    ave_diff_tot = 0.0
    quad_diff_tot = 0.0
    for i in xrange(1, molecule1+1):
      for j in xrange(i, molecule1+1):
        d1, d2, d3, d4 = lmp_io.load_target_and_cg_rdf("rdf.%d.%d" % (i, j), "rdf_%d.%d.%d" % (iter-1, i, j))  
        ave_diff_tot += d3 
        quad_diff_tot += d4
        #print iter, i, j, "ave.: %f, quad.: %f" % (d3, d4)
    print iter, "Average difference (total): %f, Squared difference (total): %f" % (ave_diff_tot, quad_diff_tot)

def add_rdf_plot(iter, molecule1, molecule2, row, column, index, fig):

  print "add_rdf_plot: ", iter, molecule1, molecule2, "d1: rdf.%d.%d" % (molecule1, molecule2), "d2: rdf_%d.%d.%d" % (iter-1, molecule1, molecule2)

  d1, d2, d3, d4 = lmp_io.load_target_and_cg_rdf("rdf.%d.%d" % (molecule1, molecule2), "rdf_%d.%d.%d" % (iter-1, molecule1, molecule2), averaging="no")
 
  ax2 = fig.add_subplot(row, column, index)
  
  ax2.plot(d1[:,0],d1[:,2], label="target %d %d" % (molecule1, molecule2))
  ax2.plot(d2[:,0],d2[:,1], label="fit iteration %d" % (iter-1))
#  ax2.plot(d2[:,0],np.absolute(d3), label="error iteration %d" % (iter-1)) #plot the error if needed:

  y_coord = (pylab.ylim())[1] - 0.1
  ax2.text(0.1, y_coord, "ave. diff: %f, quad. diff: %f" % (np.average(np.absolute(d3)), np.average(d4)), style='italic') 
  
  set_small_legend()

def calc_ave_press(iter, tag="Press"):
  d1,d2 = lmp_io.load_quantity_from_file("new_CG.prod%d.log" % (iter-1), tag)

  offset = 100

  pave = np.average(d2[100:])
  pstdev = np.std(d2[100:])

  print "READ: new_CG.prod%d.log" % (iter-1)
  print "%s information iteration #%d, average pressure: %f, stdev: %f, initial values: %f %f %f" % (tag, iter-1,pave,pstdev,d2[0],d2[1],d2[2]) 

def get_pressure(iter, tag):
  d1,d2 = lmp_io.load_quantity_from_file("new_CG.prod%d.log" % (iter-1), tag)
  print "READ: new_CG.prod%d.log" % (iter-1)

  offset = 100

  pave = np.average(d2[100:])
  pstdev = np.std(d2[100:])

  print "%s information iteration #%d, average pressure: %f, stdev: %f, initial values: %f %f %f" % (tag, iter-1,pave,pstdev,d2[0],d2[1],d2[2])

  return pave, pstdev, d1, d2

def add_pressure_plot(iter, row, column, index, fig, tag="Press"):

  pave, pstdev, d1, d2 = get_pressure(iter, tag)

  print row,column,index
  
  ax2 = fig.add_subplot(row, column, index)
  
  ax2.plot(d1,d2, label="%s iteration %d (LAMMPS-based)" % (tag, iter-1))
  ax2.plot(d1,smooth_data(d2, window_len=(len(d1)/50)))
  ax2.text(0, 1, "average: %f, stdev: %f" % (pave, pstdev), style='italic', bbox={'facecolor':'white', 'alpha':1, 'pad':10}, transform = ax2.transAxes)

  pylab.legend(loc=4)

#def add_pos_plot(iter, row, column, index, fig):
#  xs, ys, zs, ts = lmp_io.load_atoms_from_file("new_CG.prod%d.log" % (iter-1), 20000)
#  ax = fig.add_subplot(row, column, index, projection='3d')
#  ax.scatter(xs, ys, zs, c='r', marker='o')
#  
#  pylab.legend(loc=4)

def analyse_and_plot_lammps_rdf_file(plot_panel, filename, ibi_iteration_number, molecule1, molecule2): 
  
  for i in [0, 5000, 100000, 250000]:
    print i
    rdf_average = lmp_io.read_lammps_rdf(filename, 3, ibi_iteration_number, timestep_limit=i, write_rdf_files=False, timestep_threshold=0)
    
    plot_panel.plot(range(0,len(rdf_average[molecule1][molecule2])),rdf_average[molecule1][molecule2], label="target %d %d step %d" % (molecule1, molecule2, i))
       
  pylab.legend(loc=4)
 

def rdf_compare(plot_panel, filename1, filename2, ibi_iteration_number, molecule1, molecule2): 
  
  i = 0
  rdf_average = lmp_io.read_lammps_rdf(filename1, 4, ibi_iteration_number, timestep_limit=i, write_rdf_files=False, timestep_threshold=0)
  rdf_average2 = lmp_io.read_lammps_rdf(filename2, 4, ibi_iteration_number, timestep_limit=i, write_rdf_files=False, timestep_threshold=0)
    
  plot_panel.plot(range(0,len(rdf_average[molecule1][molecule2])),rdf_average[molecule1][molecule2], label="previous: target %d %d step %d" % (molecule1, molecule2, i))
  plot_panel.plot(range(0,len(rdf_average2[molecule1][molecule2])),rdf_average2[molecule1][molecule2], label="current: target %d %d step %d" % (molecule1, molecule2, i))
    
  pylab.legend(loc=4)
  


if __name__ == "__main__":

  if len(sys.argv) == 0:
    print """
    LAMMPS Plotting Tool

    USAGE:
    python <script> pzz <last_iteration>
    python <script> pressures <last_iteration>
    python <script> rdfs <last_iteration> <optional: atom1> <optional:atom2>
    python <script> pots <last_iteration> <optional: atom1> <optional:atom2>
    python <script> ibi_iteration <iteration> <optional: atom1> <optional:atom2>
    python <script> lammps_rdf <iteration> <optional: atom1> <optional:atom2>
    python <script> lammps_rdf <iteration> <optional: num_atom_types>
    python <script> one_pot <filename>
  
    NOTE: ibi_iteration should be run after IBI.py has been run, and use the 
    iteration number with which the newly generated pot files are tagged.

    """
    sys.exit()
  
  mode = sys.argv[1] 
  iter = 0
  
  if mode != "one_pot":
    iter = int(sys.argv[2])
  
  if mode == "txt_pres":
    for i in xrange(2,iter+1):
      a,b,c,d = get_pressure(i,"Press")
      a,b,c,d = get_pressure(i,"Pzz")
    sys.exit()

  if mode == "txt_rdf":
    for i in xrange(2,iter+1):
      txt_rdf(i, int(sys.argv[3]), int(sys.argv[4]))
    sys.exit()
 
  fig = pylab.plt.figure("Iteration: %d" % (iter))
  
  #TODO: make a plotting mode with pressure value for individual interactions, based on ibi_iteration.  

  if mode == "one_pot":
    add_one_potential_plot(sys.argv[2],1,1,1,fig)


  if mode == "full_pres":
    add_pressure_plot(iter, 2, 1, 1, fig, "Pzz")
    add_pressure_plot(iter, 2, 1, 2, fig, "Press")
  
  if mode == "pzz":
    istart = max(2,iter-7)
    for i in xrange(istart,iter+1):
      add_pressure_plot(i, 2, min(iter/2,4), i-istart+1, fig, "Pzz")

  if mode == "pzz_all":
    for i in xrange(1,199):
      calc_ave_press(i, "Press")
      
  if mode == "pressures":
    istart = max(2,iter-7)
    for i in xrange(istart,iter+1):
      add_pressure_plot(i, 2, min(iter/2,4), i-istart+1, fig)

  if mode == "rdfs_charged":
    add_rdf_plot(iter, 1, 3, 2, 2, 1, fig)
    add_rdf_plot(iter, 2, 3, 2, 2, 2, fig)
    add_rdf_plot(iter, 1, 4, 2, 2, 3, fig) 
    add_rdf_plot(iter, 2, 4, 2, 2, 4, fig)
     
 
  if mode == "rdfs" or mode == "pots":
    istart = max(1,iter-8)
    if mode == "rdfs":
      istart += 1
    atom1 = 1
    atom2 = 1
    if len(sys.argv) == 5:
      atom1 = int(sys.argv[3])
      atom2 = int(sys.argv[4])
    for i in xrange(istart,iter+1):
      if mode == "rdfs":
        add_rdf_plot(i, atom1, atom2, 2, (iter+2-istart)/2, i-istart+1, fig)
      if mode == "pots":
        add_potential_plot(i, atom1, atom2, 2, (iter+2-istart)/2, i-istart+1, fig)
 
  if mode == "ibi_iteration":
    if len(sys.argv) == 5:
      print "Single interaction per iteration checker."
      add_potential_plot(iter, int(sys.argv[3]), int(sys.argv[4]), 2, 2, 1, fig)
      add_rdf_plot(iter-1, int(sys.argv[3]), int(sys.argv[4]), 2, 2, 2, fig)
      add_pressure_plot(iter-1, 2, 2, 3, fig)
    
    elif len(sys.argv) == 3:
      k = 0
      for i in xrange(1,3):
        for j in xrange(i,3):
          print k
          k += 1
          add_potential_plot(iter, i, j, 3, 4, k*2-1, fig)
          add_rdf_plot(iter, i, j, 3, 4, k*2, fig)
    else:
      sys.exit("the ibi_iteration mode works with either 2 or 4 parameters in total.")
  
  elif mode == "rdf_compare":
    atom1 = int(sys.argv[3])
    atom2 = int(sys.argv[4])
    plot_panel = fig.add_subplot(1, 1, 1)
    rdf_compare(plot_panel, "tmp.%d.rdf" % (iter), "tmp.1.rdf", iter, atom1, atom2)

  elif mode == "lammps_rdf":
    if len(sys.argv)>4:
      atom1 = int(sys.argv[3])
      atom2 = int(sys.argv[4])
      plot_panel = fig.add_subplot(1, 1, 1)
      analyse_and_plot_lammps_rdf_file(plot_panel, "tmp.%d.rdf" % (iter), iter, atom1, atom2)
    elif len(sys.argv) == 4:
      k=1
      rdf_average = lmp_io.read_lammps_rdf("tmp.%d.rdf" % (iter), int(sys.argv[3]), iter, timestep_limit=200000, write_rdf_files=False, timestep_threshold=0)
      for i in range(1,int(sys.argv[3])):
        for j in range(i,int(sys.argv[3])):
          # Create panel
          plot_panel = fig.add_subplot(int(sys.argv[3]),(int(sys.argv[3])+1)/2, k)
          
          # plot target RDF
          d1 = np.loadtxt("rdf.%d.%d" % (i,j))
          print "add_rdf_plot: ", iter, i, j, "d1: rdf.%d.%d" % (i,j)
          #plot_panel.plot(d1[:,0],d1[:,2], label="target %d %d" % (i,j))
          plot_panel.plot(xrange(0,len(d1)),d1[:,2], label="target %d %d" % (i,j))

          # plot CG approximation
          plot_panel.plot(xrange(0,len(rdf_average[i][j])),rdf_average[i][j], label="CG %d %d" % (i,j))
          k += 1
          pylab.legend(loc=4)          
  
  pylab.show()
