# -*- coding: utf-8 -*-
# 
# Copyright (C) University College London, 2013, all rights reserved.
# 
# This file is part of FabMD and is CONFIDENTIAL. You may not work 
# with, install, use, duplicate, modify, redistribute or share this
# file, or any part thereof, other than as allowed by any agreement
# specifically made by you with University College London.
# 

from fab import *

@task
def namd(config,**args):
  """Submit a NAMD job to the remote queue.
  The job results will be stored with a name pattern as defined in the environment,
  e.g. cylinder-abcd1234-legion-256
  config : config directory to use to define geometry, e.g. config=cylinder
  Keyword arguments:
  cores : number of compute cores to request
  images : number of images to take
  steering : steering session i.d.
  wall_time : wall-time job limit
  memory : memory per node
  """
  with_config(config)
  execute(put_configs,config)
  job(dict(script='namd',
  cores=32, wall_time='1:00:00',memory='2G'),args)

@task
def bac_archer(config,**args):
  """Submit ensemble NAMD equilibration-simulation jobs to the ARCHER.
  The job results will be stored with a name pattern as defined in the environment,
  e.g. cylinder-abcd1234-legion-256
  config : config directory to use to define geometry, e.g. config=cylinder
  Keyword arguments:
  cores : number of compute cores to request
  stages : this is usually 11 for equilibration (WT case) and 4 for simulation
  wall_time : wall-time job limit
  memory : memory per node
  """
  with_config(config)
  execute(put_configs,config)
  job(dict(script='bac-archer',
  cores=480, stages_eq=11, stages_sim=4, replicas=5, wall_time='24:00:00',memory='2G'),args)


@task
def namd_eq(config,**args):
  """Submit ensemble NAMD equilibration job to the remote queue.
  The job results will be stored with a name pattern as defined in the environment,
  e.g. cylinder-abcd1234-legion-256
  config : config directory to use to define geometry, e.g. config=cylinder
  Keyword arguments:
  cores : number of compute cores to request
  stages : this is always equal to 2 for equilibration jobs
  wall_time : wall-time job limit
  memory : memory per node
  """
  with_config(config)
  execute(put_configs,config)
  job(dict(script='namd-eq-archer',
  cores=480, stages=2, replicas=5, wall_time='24:00:00',memory='2G'),args)

@task
def namd_sim(config,**args):
  """Submit ensemble NAMD simulation job to the remote queue.
  The job results will be stored with a name pattern as defined in the environment,
  e.g. cylinder-abcd1234-legion-256
  config : config directory to use to define geometry, e.g. config=cylinder
  Keyword arguments:
  cores : number of compute cores to request
  stages : this is always equal to 2 for equilibration jobs
  wall_time : wall-time job limit
  memory : memory per node
  """
  with_config(config)
  execute(put_configs,config)
  job(dict(script='namd-sim-archer',
  cores=480, stages=4, replicas=5, wall_time='24:00:00',memory='2G'),args)

@task
def find_namd_executable():
  namd_modules = probe('namd')
  print namd_modules
  for line in namd_modules.split("\n"):
    if "(" in line:
      print line
      stripped_line = (line.strip()).split("(")
      print "which namd2"
      namd = run("module load %s && which namd2" % stripped_line[0])
      print "FabMD: NAMD executable is located at:", namd
      return namd
  print "No relevant modules found. Trying a basic which command."    
  namd = run("which namd2")
  return namd

@task
def dir_structure(num_rep,path):
    """ Creates appropriate directory structure for ensemble simulations from the initial directory structure created by BAC builder.
        num_rep is number of replicas desired and path is the full path of the original directory created by BAC builder. """

    if len(num_rep)<1:
      print "error: number of replicas not defined."
      sys.exit()

    if len(path)<1:
      print "error: path of rep0 not defined."
      sys.exit()

    print "restructuring directory for ensemble simulations"
    local("mkdir %s/replicas; mkdir %s/replicas/rep1" % (path, path))
    for d in ['data','dcds','equilibration','simulation','analysis_scripts']:
        local("mv %s/%s %s/replicas/rep1" % (path, d, path))

    #local("mv %s/data %s/replicas/rep1" % (path, path))
    #local("mv %s/dcds %s/replicas/rep1"% (path, path))
    #local("mv %s/equilibration %s/replicas/rep1" % (path, path))
    #local("mv %s/simulation %s/replicas/rep1" % (path, path))
    #local("mv %s/analysis_scripts %s/replicas/rep1" % (path, path))
    local("mkdir %s/replicas/rep1/fe-calc; mkdir %s/replicas/rep1/fe-calc/build %s/replicas/rep1/fe-calc/amber_traj" % (path, path, path))
    for x in xrange(2, int(num_rep) + 1):
        local("cp -r %s/replicas/rep1 %s/replicas/rep%s" % (path, path, x))

