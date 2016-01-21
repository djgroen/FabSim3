# 
# This source file is part of the FabSim software toolkit, which is distributed under the BSD 3-Clause license. 
# Please refer to LICENSE for detailed information regarding the licensing.
#
# Implements fab <machine> analyze: a simplistic data plotting routine.

from ..fab import *

@task
def analyze(name,title="fab analyze plot", x_column=0, y_column=1, plot_file_name="plot.png"):
  """
  Performs some trivial data analysis.
  """
  import matplotlib.pyplot as plt
  import numpy as np

  source_data = np.loadtxt(name)
  plt.plot(source_data[:,x_column], source_data[:,y_column])

  plt.xlabel('X')
  plt.ylabel('Y')
  plt.title(title)
  plt.grid(True)
  plt.savefig(plot_file_name)
  plt.show()
