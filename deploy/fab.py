# -*- coding: utf-8 -*-
# 
# Copyright (C) University College London, 2013, all rights reserved.
# 
# This file is part of FabMD and is CONFIDENTIAL. You may not work 
# with, install, use, duplicate, modify, redistribute or share this
# file, or any part thereof, other than as allowed by any agreement
# specifically made by you with University College London.
# 

from templates import *
from machines import *
from fabric.contrib.project import *
from xml.etree import ElementTree
import time
import re
import numpy as np
import yaml
import tempfile
from pprint import PrettyPrinter
pp=PrettyPrinter()


@task
def stat():
    """Check the remote message queue status"""
    #TODO: Respect varying remote machine queue systems.
    return run(template("$stat -u $username"))

@task
def monitor():
    """Report on the queue status, ctrl-C to interrupt"""
    while True:
        execute(stat)
        time.sleep(120)
        
        
def check_complete():
  """Return true if the user has no queued jobs"""
  return stat()==""
     
@task
def wait_complete():
  """Wait until all jobs currently qsubbed are complete, then return"""
  time.sleep(120)
  while not check_complete():
        time.sleep(120)

def with_template_job():
    """
    Determine a generated job name from environment parameters, and then define additional environment parameters based on it.
    """
    name=template(env.job_name_template)
    if env.get('label'):
        name='_'.join((env['label'],name))
    with_job(name)

def with_job(name):
    """Augment the fabric environment with information regarding a particular job name.
    Definitions created:
    job_results: the remote location where job results should be stored
    job_results_local: the local location where job results should be stored
    """
    env.name=name
    env.job_results=env.pather.join(env.results_path,name)
    env.job_results_local=os.path.join(env.local_results,name)
    env.job_results_contents=env.pather.join(env.job_results,'*')
    env.job_results_contents_local=os.path.join(env.job_results_local,'*')

    #env.job_name_template_sh=template("%s.sh" % env.job_name_template)

def with_template_config():
    """
    Determine the name of a used or generated config from environment parameters, and then define additional environment parameters based on it.
    """
    with_config(template(env.config_name_template))

def with_config(name):
    """Internal: augment the fabric environment with information regarding a particular configuration name.
    Definitions created:
    job_config_path: the remote location where the config files for the job should be stored
    job_config_path_local: the local location where the config files for the job may be found
    """
    env.config=name
    env.job_config_path=env.pather.join(env.config_path,name)
    env.job_config_path_local=os.path.join(env.local_configs,name)
    env.job_config_contents=env.pather.join(env.job_config_path,'*')
    env.job_config_contents_local=os.path.join(env.job_config_path_local,'*')

def with_profile(name):
    """Internal: augment the fabric environment with information regarding a particular profile name.
    Definitions created:
    job_profile_path: the remote location where the profile should be stored
    job_profile_path_local: the local location where the profile files may be found
    """
    env.profile=name
    env.job_profile_path=env.pather.join(env.profiles_path,name)
    env.job_profile_path_local=os.path.join(env.local_profiles,name)
    env.job_profile_contents=env.pather.join(env.job_profile_path,'*')
    env.job_profile_contents_local=os.path.join(env.job_profile_path_local,'*')

@task
def fetch_configs(config=''):
    """
    Fetch config files from the remote, via rsync.
    Specify a config directory, such as 'cylinder' to copy just one config.
    Config files are stored as, e.g. cylinder/config.dat and cylinder/config.xml
    Local path to use is specified in machines_user.json, and should normally point to a mount on entropy,
    i.e. /store4/blood/username/config_files
    This method is not intended for normal use, but is useful when the local machine cannot have an entropy mount,
    so that files can be copied to a local machine from entropy, and then transferred to the compute machine,
    via 'fab entropy fetch_configs; fab legion put_configs'
    """
    with_config(config)
    local(template("rsync -pthrvz $username@$remote:$job_config_path/ $job_config_path_local"))

@task
def put_configs(config=''):
    """
    Transfer config files to the remote.
    For use in launching jobs, via rsync.
    Specify a config directory, such as 'cylinder' to copy just one configuration.
    Config files are stored as, e.g. cylinder/config.dat and cylinder/config.xml
    Local path to find config directories is specified in machines_user.json, and should normally point to a mount on entropy,
    i.e. /store4/blood/username/config_files
    If you can't mount entropy, 'fetch_configs' can be useful, via 'fab entropy fetch_configs; fab legion put_configs'
    """

    with_config(config)
    run(template("mkdir -p $job_config_path"))
    rsync_project(local_dir=env.job_config_path_local+'/',remote_dir=env.job_config_path)

@task
def put_results(name=''):
    """
    Transfer result files to a remote.
    Local path to find result directories is specified in machines_user.json.
    This method is not intended for normal use, but is useful when the local machine cannot have an entropy mount,
    so that results from a local machine can be sent to entropy, via 'fab legion fetch_results; fab entropy put_results'
    """
    with_job(name)
    run(template("mkdir -p $job_results"))
    rsync_project(local_dir=env.job_results_local+'/',remote_dir=env.job_results)

@task
def fetch_results(name='',regex='',debug=False):
    """
    Fetch results of remote jobs to local result store.
    Specify a job name to transfer just one job.
    Local path to store results is specified in machines_user.json, and should normally point to a mount on entropy,
    i.e. /store4/blood/username/results.
    If you can't mount entropy, 'put results' can be useful,  via 'fab legion fetch_results; fab entropy put_results'
    """
    
    if debug:
        pp.pprint(env)
    with_job(name)
    local(template("rsync -pthrvz $username@$remote:$job_results/%s $job_results_local" % regex))

@task
def clear_results(name=''):
    """Completely wipe all result files from the remote."""
    with_job(name)
    run(template('rm -rf $job_results_contents'))

@task
def fetch_profiles(name=''):
    """
    Fetch results of remote jobs to local result store.
    Specify a job name to transfer just one job.
    Local path to store results is specified in machines_user.json, and should normally point to a mount on entropy,
    i.e. /store4/blood/username/results.
    If you can't mount entropy, 'put results' can be useful,  via 'fab legion fetch_results; fab entropy put_results'
    """
    with_profile(name)
    local(template("rsync -pthrvz $username@$remote:$job_profile_path/ $job_profile_path_local"))

@task
def put_profiles(name=''):
    """
    Transfer result files to a remote.
    Local path to find result directories is specified in machines_user.json.
    This method is not intended for normal use, but is useful when the local machine cannot have an entropy mount,
    so that results from a local machine can be sent to entropy, via 'fab legion fetch_results; fab entropy put_results'
    """
    with_profile(name)
    run(template("mkdir -p $job_profile_path"))
    rsync_project(local_dir=env.job_profile_path_local+'/',remote_dir=env.job_profile_path)

@task
def setup_fabric_dirs(name=''):
    """
    Creates the necessary fab dirs remotely.
    """
    run(template('mkdir -p $config_path'))
    run(template('mkdir -p $results_path'))
    run(template('mkdir -p $scripts_path'))

def update_environment(*dicts):
    for adict in dicts:
        env.update(adict)

def calc_nodes():
  # If we're not reserving whole nodes, then if we request less than one node's worth of cores, need to keep N<=n

  env.coresusedpernode=env.corespernode
  if int(env.coresusedpernode)>int(env.cores):
    env.coresusedpernode=env.cores
  env.nodes=int(env.cores)/int(env.coresusedpernode)


def job(*option_dictionaries):
    """Internal low level job launcher.
    Parameters for the job are determined from the prepared fabric environment
    Execute a generic job on the remote machine. Use lammps, regress, or test instead."""
    
    update_environment(*option_dictionaries)
    with_template_job()

    # If the replicas parameter is defined, then we are dealing with an ensemble job. We will calculate the 
    # cores per replica by dividing up the total core count.
    if 'replicas' in option_dictionaries[0].keys():
        env.cores_per_replica = int(env.cores) / int(env.replicas)


    # Use this to request more cores than we use, to measure performance without sharing impact
    if env.get('cores_reserved')=='WholeNode' and env.get('corespernode'):
        env.cores_reserved=(1+(int(env.cores)-1)/int(env.corespernode))*int(env.corespernode)

    # If cores_reserved is not specified, temporarily set it based on the same as the number of cores
    # Needs to be temporary if there's another job with a different number of cores which should also be defaulted to.
    with settings(cores_reserved=env.get('cores_reserved') or env.cores):
        calc_nodes()
        if env.node_type:
            env.node_type_restriction=template(env.node_type_restriction_template)
        
        if 'replica_index' in option_dictionaries[0].keys():
            print "replica_index found."
            env.name = env.name + "_" + str(env.replica_index)

        if 'lambda_index' in option_dictionaries[0].keys():
            print "lambda_index found."
            env.name = env.name + "_" + str(env.lambda_index)
    
        env['job_name']=env.name[0:env.max_job_name_chars]
        with settings(cores=1):
            calc_nodes()
            env.run_command_one_proc=template(env.run_command)
        calc_nodes()
        env.run_command=template(env.run_command)
        if 'run_ensemble_command' in option_dictionaries[0].keys():
            env.run_ensemble_command=template(env.run_ensemble_command)
	if 'run_ensemble_command_ties' in option_dictionaries[0].keys():

            pp.pprint(env)

	    env.run_ensemble_command_ties=template(template(env.run_ensemble_command_ties))

        env.job_script=script_templates(env.batch_header,env.script)

        env.dest_name=env.pather.join(env.scripts_path,env.pather.basename(env.job_script))
        put(env.job_script,env.dest_name)
        
        if 'remote_path' in option_dictionaries[1].keys():
            print "remote_path found."
            env.job_results = env.remote_path
        
        run(template("mkdir -p $job_results && cp $dest_name $job_results && chmod u+x $dest_name")) #bundled 3 ssh sessions into one to improve performance.
        with tempfile.NamedTemporaryFile() as tempf:
            tempf.write(yaml.dump(dict(env)))
            tempf.flush() #Flush the file before we copy it.
            put(tempf.name,env.pather.join(env.job_results,'env.yml'))
        # Allow option to submit all preparations, but not actually submit the job
        if not env.get("noexec",False):
                   with cd(env.job_results):
                       with prefix(env.run_prefix):
                           run(template("$job_dispatch $dest_name"))

def input_to_range(arg,default):
    ttype=type(default)
    gen_regexp="\[([\d\.]+):([\d\.]+):([\d\.]+)\]" #regexp for a array generator like [1.2:3:0.2]
    if not arg:
        return [default]
    match=re.match(gen_regexp,str(arg))
    if match:
        vals=list(map(ttype,match.groups()))
        if ttype==int:
            return range(*vals)
        else:
            return np.arange(*vals)

    return [ttype(arg)]

@task
def get_running_location(job=None):
    """
    Returns the node name where a given job is running.
    """
    if job:
        with_job(job)
    env.running_node=run(template("cat $job_results/env_details.asc"))

def manual(cmd):
    #From the fabric wiki, bypass fabric internal ssh control
    commands=env.command_prefixes[:]
    if env.get('cwd'):
        commands.append("cd %s"%env.cwd)
    commands.append(cmd)
    manual_command=" && ".join(commands)
    pre_cmd = "ssh -Y -p %(port)s %(user)s@%(host)s " % env
    local(pre_cmd + "'"+manual_command+"'", capture=False)

#def manual_gsissh(cmd):
#    #From the fabric wiki, bypass fabric internal ssh control
#    commands=env.command_prefixes[:]
#    if env.get('cwd'):
#        commands.append("cd %s"%env.cwd)
#    commands.append(cmd)
#    manual_command=" && ".join(commands)
#
#    pre_cmd = "gsissh -p %(port)s %(host)s " % env
#    local(pre_cmd + "'"+manual_command+"'", capture=False)
#    
def run(cmd):
#    if env.manual_gsissh:
#        return manual_gsissh(cmd)
#    else if env.manual_ssh:
    if env.manual_ssh:
        return manual(cmd)
    else:
        return fabric.api.run(cmd)
        
def put(src,dest):
    if env.manual_ssh:
        env.manual_src=src
        env.manual_dest=dest
        local(template("scp $manual_src $user@$host:$manual_dest"))
    else:
        fabric.api.put(src,dest)

@task
def blackbox(script='ibi.sh', args=''):
    """ black-box script execution. """
    local("%s %s" % (os.path.join(env.localroot,'blackbox', script), args))

@task
def probe(label="undefined"):
    """ Scans a remote site for the presence of certain software. """
    return run("module avail 2>&1 | grep %s" % label)
    
@task
def archive(prefix, archive_location):
    """ Cleans results directories of core dumps and moves results to archive locations. """

    if len(prefix)<1:
      print "error: no prefix defined."
      sys.exit()

    print "LOCAL %s %s %s*" % (env.local_results, prefix, archive_location)
    local("rm -f %s/*/core" % (env.local_results))
    local("mv -i %s/%s* %s/" % (env.local_results, prefix, archive_location))
    
    
    parent_path = os.sep.join(env.results_path.split(os.sep)[:-1])
    
    print "REMOTE MOVE: mv %s/%s %s/Backup" % (env.results_path, prefix, parent_path)
    run("mkdir -p %s/Backup" % (parent_path))
    run("mv -i %s/%s* %s/Backup/" % (env.results_path, prefix, parent_path))

@task
def print_config(args=''):
    """ Prints local environment """
    for x in env:
        print x,':',env[x]
