from fab import *
import numpy as np

@task
def dir_structure(num_rep,path):
    """ Creates appropriate directory structure for ensemble simulations from the initial directory structure created by BAC builder """

    if len(num_rep)<1:
      print "error: number of replicas not defined."
      sys.exit()
    
    if len(path)<1:
      print "error: path of rep0 not defined."
      sys.exit()

    print "restructuring directory for ensemble simulations"# % (env.local_results, prefix, archive_location)
    #local("cd %s" % (path))
    local("mkdir %s/replicas; mkdir %s/replicas/rep1" % (path, path))
    local("mv %s/data %s/replicas/rep1" % (path, path))
    local("mv %s/dcds %s/replicas/rep1"% (path, path))
    local("mv %s/equilibration %s/replicas/rep1" % (path, path))
    local("mv %s/simulation %s/replicas/rep1" % (path, path))
    local("mv %s/analysis_scripts %s/replicas/rep1" % (path, path))
    local("mkdir %s/replicas/rep1/fe-calc; mkdir %s/replicas/rep1/fe-calc/build %s/replicas/rep1/fe-calc/amber_traj" % (path, path, path))
    #local("cd %s/replicas" % (path))
    for x in xrange(2, int(num_rep) + 1):
    	local("cp -r %s/replicas/rep1 %s/replicas/rep%s" % (path, path, x))



