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
def bac_namd_archerlike(config,**args):
  """Submit ensemble NAMD equilibration-simulation jobs to the ARCHER or similar machines.
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
  job(dict(script=env.bac_ensemble_namd_script,
  cores=480, stages_eq=11, stages_sim=4, replicas=5, wall_time='24:00:00',memory='2G'),args)

@task
def bac_namd_hartreelike(config,**args):
  """Submits ensemble NAMD equilibration-simulation jobs to HARTREE or similar machines.
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
  update_environment(args)
 # env.job_name_template_sh=template("%s%s.sh" % env.job_name_template,$replica_index)
  if not env.get('replicas'):
    env.update(dict(replicas=25)) 
    print "WARNING: replicas argument not specified. Setting a default value of", env.replicas   
  #  sys.exit()

  for ri in xrange(1,int(env.replicas)+1):
    env.job_name_template_sh=template("%s_%s.sh" % (env.job_name_template,str(ri)))
    print env.job_name_template_sh
    env.job_script=script_templates(env.batch_header,env.script,str(ri))
    print env.job_script
    job(dict(script=env.bac_ensemble_namd_script,
    cores=384, stages_eq=11, stages_sim=4, wall_time='6:00', memory='2G', replicas=env.replicas, replica_index=ri),args)

@task
def bac_nmode_archerlike(config,**args):
  """Submit ensemble NMODE/MMPB(GB)SA jobs to the ARCHER or similar machines.
  The job results will be stored with a name pattern as defined in the environment,
  e.g. cylinder-abcd1234-legion-256
  config : config directory to use to define geometry, e.g. config=cylinder
  Keyword arguments:
  cores : number of compute cores to request
  wall_time : wall-time job limit
  memory : memory per node
  """
  with_config(config)
  execute(put_configs,config)
  job(dict(script=env.bac_ensemble_nmode_script,
  cores=240, replicas=5, wall_time='12:00:00',memory='2G'),args)

@task
def bac_nm_remote_archerlike(**args):
  """Submit ensemble NMODE/MMPB(GB)SA jobs to the ARCHER or similar machines, 
  when the simulation data is already on the remote machine.
  The job results will be stored with a name pattern as defined in the environment,
  e.g. cylinder-abcd1234-legion-256
  config : config directory to use to define geometry, e.g. config=cylinder
  Keyword arguments:
  cores : number of compute cores to request
  wall_time : wall-time job limit
  memory : memory per node
  """
  with_config('')
  #execute(put_configs,config)

  job(dict(config='',script=env.bac_ensemble_nm_remote_script,
  cores=240, replicas=5, wall_time='12:00:00',memory='2G'),args)

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
    local("mv %s/fe-calc/build/* %s/build/ ; rm -r %s/fe-calc" % (path, path, path))
    local("mkdir %s/replicas/rep1/fe-calc" % path)
    for x in xrange(2, int(num_rep) + 1):
        local("cp -r %s/replicas/rep1 %s/replicas/rep%s" % (path, path, x))

