# -*- coding: utf-8 -*-
# 
# This source file is part of the FabSim software toolkit, which is distributed under the BSD 3-Clause license. 
# Please refer to LICENSE for detailed information regarding the licensing.
#
# This file contains FabSim definitions specific to FabBioMD.

from ..fab import *

# Add local script, blackbox and template path.
add_local_paths("BioMD")

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
  update_environment(args)
  if not env.get('cores'):
    env.cores=32
  with_config(config)
  execute(put_configs,config)
  job(dict(script='namd',
  wall_time='1:00:00',memory='2G',job_type='parallel',job_class='micro'),args)

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
  update_environment(args)
  if not env.get('cores'):
    env.cores=2400
  with_config(config)
  execute(put_configs,config)
  job(dict(script=env.bac_ensemble_namd_script,
  stages_eq=11, stages_sim=1, replicas=25, wall_time='24:00:00',memory='2G'),args)

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
  mem : memory of nodes requested for Bluewonder Phase 1. By default is 32000,
  but higher memory nodes can be requested by using other values. For eg. use 64000 for >64 GB memory nodes.
  """
  update_environment(args)
  if not env.get('cores'):
    env.cores=384
  if not env.get('replicas'):
    env.update(dict(replicas=25)) 
    print "WARNING: replicas argument not specified. Setting a default value of", env.replicas   
  #  sys.exit()
  with_config(config)
  execute(put_configs,config)

  for ri in xrange(1,int(env.replicas)+1):
    job(dict(script=env.bac_ensemble_namd_script,
    stages_eq=11, stages_sim=1, wall_time='6:00', memory='2G', mem=25000, replicas=env.replicas, replica_index=ri),args)

@task
def bac_ties_archerlike(config,**args):
  """Creates appropriate directory structure for TIES calculation given that it is already restructured using dir_structure function of FabSim.
  """
  update_environment(args)
  # Workaround to ensure env.cores is set before we calculate cores_per_lambda.
  if not env.get('cores'):
    env.cores=6240
  if not env.get('replicas'):
    env.replicas=5
  if not env.get('lambda_list'):
    env.update(dict(lambda_list= '0.00 0.05 0.10 0.20 0.30 0.40 0.50 0.60 0.70 0.80 0.90 0.95 1.00'))
    print "WARNING: lambda_list argument not specified. Setting a default value of", env.lambda_list

  with_config(config)
  execute(put_configs,config)

  env.cores_per_lambda = int(env.cores) / len(env.lambda_list.split(" "))
  env.cores_per_replica_per_lambda = int(env.cores_per_lambda) / int(env.replicas)

  job(dict(script=env.bac_ties_script, stages_eq=11, stages_sim=1, wall_time='12:00:00', memory='2G'),args)

#  for i in env.lambda_list.split(" "):
#    run("rsync -avz --exclude 'LAMBDA_*' %s/ %s/LAMBDA_%.2f/" % (env.job_config_path, env.job_config_path, float(i)))
#    job(dict(script=env.bac_ties_script,cores=960, stages_eq=11, stages_sim=1, replicas=10, lambda_list=env.lambda_list, lambda_index='%.2f' % float(i), wall_time='12:00:00', memory='2G'),args)

@task
def bac_namd_supermuclike(config,**args):
  """Submit ensemble NAMD equilibration-simulation jobs to the SuperMUC or similar machines.
  The job results will be stored with a name pattern as defined in the environment,
  e.g. cylinder-abcd1234-legion-256
  config : config directory to use to define geometry, e.g. config=cylinder
  Keyword arguments:
  cores : number of compute cores to request
  stages : this is usually 11 for equilibration (WT case) and 4 for simulation
  wall_time : wall-time job limit
  memory : memory per node
  """
  update_environment(args)
  if not env.get('cores'):
    env.cores=7000
  if not env.get('replicas'):
    env.replicas=25
  calc_nodes()
  env.nodes_new = "%s" % (int(env.nodes)+1) 
  env.cores_per_replica = int(env.cores) / int(env.replicas)
  if not env.get('nodes_per_replica'):
    env.update(dict(nodes_per_replica = int(env.cores_per_replica) / int(env.corespernode)))
   
  with_config(config)
  local("cp %s/redis_header.txt %s" % (env.local_templates_path[-1], env.job_config_path_local))
  execute(put_configs,config)
  
  job(dict(script=env.bac_ensemble_namd_script,
  stages_eq=11, stages_sim=1, wall_time='06:00:00',memory='2G', job_type='MPICH', job_class='general', island_count='1', nodes_new=env.nodes_new),args)

@task
def bac_ties_supermuclike(config,**args):
  """Creates appropriate directory structure for TIES calculation given that it is already restructured using dir_structure function of FabSim.
  """
  update_environment(args)
  # Workaround to ensure env.cores is set before we calculate cores_per_lambda.
  if not env.get('cores'):
    env.cores=18200
  if not env.get('replicas'):
    env.replicas=5
  if not env.get('lambda_list'):
    env.update(dict(lambda_list= '0.00 0.05 0.10 0.20 0.30 0.40 0.50 0.60 0.70 0.80 0.90 0.95 1.00'))
    print "WARNING: lambda_list argument not specified. Setting a default value of", env.lambda_list
 
  env.cores_per_lambda = int(env.cores) / len(env.lambda_list.split(" "))
  env.cores_per_replica_per_lambda = int(env.cores_per_lambda) / int(env.replicas)
  
  if not env.get('nodes_per_replica_per_lambda'):
    env.update(dict(nodes_per_replica_per_lambda = int(env.cores_per_replica_per_lambda) / int(env.corespernode)))
  calc_nodes()
  env.nodes_new = "%s" % (int(env.nodes)+1) 
  
  with_config(config)
  local("cp %s/redis_header.txt %s" % (env.local_templates_path[-1], env.job_config_path_local))
  execute(put_configs,config)
 
  job(dict(script=env.bac_ties_script, stages_eq=11, stages_sim=1, wall_time='06:00:00', memory='2G', job_type='MPICH', job_class='general', island_count='1', nodes_new=env.nodes_new),args)

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
  update_environment(args)
  if not env.get('cores'):
    env.cores=240
  with_config(config)
  execute(put_configs,config)
  job(dict(script=env.bac_ensemble_nmode_script,
  replicas=5, wall_time='12:00:00',memory='2G'),args)

@task
def bac_nmode_hartreelike(config,**args):
  """Submits ensemble NMODE/MMPB(GB)SA equilibration-simulation jobs to HARTREE or similar machines.
  The job results will be stored with a name pattern as defined in the environment,
  e.g. cylinder-abcd1234-legion-256
  config : config directory to use to define geometry, e.g. config=cylinder
  Keyword arguments:
  cores : number of compute cores to request
  stages : this is usually 11 for equilibration (WT case) and 4 for simulation
  wall_time : wall-time job limit
  memory : memory per node
  mem : memory of nodes requested for Bluewonder Phase 1. By default is 32000,
  but higher memory nodes can be requested by using other values. For eg. use 64000 for >64 GB memory nodes.
  """
  update_environment(args)
  if not env.get('cores'):
    env.cores=24
  if not env.get('replicas'):
    env.update(dict(replicas=25)) 
    print "WARNING: replicas argument not specified. Setting a default value of", env.replicas   
  #  sys.exit()
  with_config(config)
  execute(put_configs,config)

  for ri in xrange(1,int(env.replicas)+1):
    job(dict(script=env.bac_ensemble_nmode_script,
    wall_time='24:00', memory='2G', mem=25000, replica_index=ri),args)

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
  remote_path : The path of root directory where all data of ensemble jobs is located; 
                to be provided by user as an argument
  """
  update_environment(args)
  if not env.get('cores'):
    env.cores=1200
  with_config('')
  #execute(put_configs,config)
  #print "$results_path"
  job(dict(config='',script=env.bac_ensemble_nm_remote_script,
  replicas=25, wall_time='24:00:00',memory='2G'),args)

@task
def bac_nm_remote_hartreelike(**args):
  """Submits ensemble NMODE/MMPB(GB)SA equilibration-simulation jobs to HARTREE or similar machines,
  when the simulation data is already on the remote machine.
  The job results will be stored with a name pattern as defined in the environment,
  e.g. cylinder-abcd1234-legion-256
  config : config directory to use to define geometry, e.g. config=cylinder
  Keyword arguments:
  cores : number of compute cores to request
  stages : this is usually 11 for equilibration (WT case) and 4 for simulation
  wall_time : wall-time job limit
  memory : memory per node
  mem : memory of nodes requested for Bluewonder Phase 1. By default is 32000,
  but higher memory nodes can be requested by using other values. For eg. use 64000 for >64 GB memory nodes.
  remote_path : The path of root directory where all data of ensemble jobs is located;
                to be provided by user as an argument
  """
  update_environment(args)
  if not env.get('cores'):
    env.cores=24
  if not env.get('replicas'):
    env.update(dict(replicas=25)) 
    print "WARNING: replicas argument not specified. Setting a default value of", env.replicas   
  #  sys.exit()

  with_config('')
  #execute(put_configs,config)
  for ri in xrange(1,int(env.replicas)+1):
    job(dict(config='',script=env.bac_ensemble_nm_remote_script,
    wall_time='24:00', memory='2G', mem=25000, replica_index=ri),args)


@task
def find_namd_executable():
  """
  Searches module system to locate a NAMD executable.
  """
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
        num_rep is number of replicas desired and path is the full path (upto rep0) of the original directory created by BAC builder. """

    if len(num_rep)<1:
      print "error: number of replicas not defined."
      sys.exit()

    if len(path)<1:
      print "error: path of rep0 not defined."
      sys.exit()

    print "restructuring directory for ensemble simulations"
    local("mkdir -p %s/replicas/rep1" % path)
    for d in ['data', 'dcds', 'analysis_scripts', 'run_scripts']:
        local("rm -r %s/%s" % (path, d))
    for d in ['equilibration','simulation']:
        local("mv %s/%s %s/replicas/rep1 2>/dev/null; true" % (path, d, path))
    local("mv %s/fe-calc/build/* %s/build/ ; rm -r %s/fe-calc" % (path, path, path))
    local("mkdir -p %s/replicas/rep1/fe-calc" % path)
    for x in xrange(2, int(num_rep) + 1):
        local("cp -r %s/replicas/rep1 %s/replicas/rep%s" % (path, path, x))
    local("cp %s/fep.tcl %s" % (env.local_templates_path[0], path))
