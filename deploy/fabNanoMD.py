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
def lammps(config,**args):
    """Submit a LAMMPS job to the remote queue.
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
    job(dict(script='lammps',
            cores=4, wall_time='0:15:0',memory='2G'),args)

#@task
#def lammps_swelling_test(config, **args):
    """Submits a set of LAMMPS jobs to the remote queue, as part of a clay swelling test."""

    #let's first try to run the exfoliated one.
    
    #lammps_in_file = 


    #with_config(config)
    #execute(put_configs,config)
    
    #loop over swelling values
    
    #update_environment(dict(job_results, job_config_path))
    #job(dict(script='lammps',
    #cores=4, wall_time='0:15:0',memory='2G'),args)

### IBI ###

@task
def do_ibi(number, outdir, pressure=1, config_name="peg", copy="yes", ibi_script="ibi.sh", atom_dir=os.path.join(env.localroot,'python')):
    """ Copy the obtained output to a work directory, do an IBI iteration and make a new config file from the resulting data. """
    ibi_in_dir = os.path.join(env.localroot,'results',outdir)
    ibi_out_dir = os.path.join(env.localroot,'output_blackbox',os.path.basename(ibi_script),outdir)
    local("mkdir -p %s" % (ibi_out_dir))
#    if copy=="yes":
#      blackbox("copy_lammps_results.sh", "%s %s %d" % (os.path.join(env.localroot,'results',outdir), os.path.join(env.localroot,'python'), int(number)))
    blackbox(ibi_script, "%s %s %s %s %s" % (atom_dir, number, pressure, ibi_in_dir, ibi_out_dir))
    if copy=="yes":
        blackbox("prepare_lammps_config.sh", "%s %s %s %d %s" % (ibi_out_dir, os.path.join(env.localroot,'config_files'), config_name, int(number)+1, atom_dir))

@task
def ibi_analysis_multi(start_iter, num_iters, outdir_prefix, outdir_suffix, ibi_script="ibi.sh", pressure=1, atom_dir=os.path.join(env.localroot,'python')):
    """ Recreate IBI analysis results based on the output files provided.
    Example use: fab hector ibi_analysis_multi:start_iter=7,num_iters=3,outdir_prefix=peg_,outdir_suffix=_hector_32 """
    si = int(start_iter)
    ni = int(num_iters)
    for i in xrange(si,si+ni):
        outdir = "%s%d%s" % (outdir_prefix,i,outdir_suffix)
        do_ibi(i, outdir, pressure, outdir_prefix, "no", ibi_script, atom_dir)

#        ibi_in_dir = os.path.join(env.localroot,'results',outdir)
#        ibi_out_dir = os.path.join(env.localroot,'ibi_output',outdir)
#        local("mkdir -p %s" % (ibi_out_dir))
#        blackbox("copy_lammps_results.sh", "%s %s %d" % (os.path.join(env.localroot,'results',"%s%d%s" % (outdir_prefix,i,outdir_suffix)), os.path.join(env.localroot,'python'), i))
#        blackbox(ibi_script, "%s %s %s %s" % (i, pressure, ibi_in_dir, ibi_out_dir))

@task
def full_ibi(config, number, outdir, config_name, pressure=0.3, ibi_script="ibi.sh", atom_dir=os.path.join(env.localroot,'python'), **args): 
    """ Performs both do_ibi and runs lammps with the newly created config file. 
    Example use: fab hector full_ibi:config=2peg4,number=3,outdir=2peg3_hector_32,config_name=2peg,cores=32,wall_time=3:0:0 """
    do_ibi(number, outdir, pressure, config_name, "yes", ibi_script, atom_dir)
    lammps(config, **args)
    wait_complete()
    fetch_results(regex="*%s*" % (config_name))

@task
def full_ibi_multi(start_iter, num_iters, config_name, outdir_suffix, pressure=0.3, script="ibi.sh", atom_dir="default", **args):
    """ Do multiple IBI iterations in one command. 
    Example use: fab hector full_ibi_multi:start_iter=7,num_iters=3,config_name=2peg,outdir_suffix=_hector_32,cores=32,wall_time=3:0:0 """

    if atom_dir == "default":
        atom_dir =  os.path.join(env.localroot,"results","%s%d%s" % (config_name,1,outdir_suffix))

    si = int(start_iter)
    ni = int(num_iters)
    
    pressure_changed = 0
    
    for i in xrange(si,si+ni):       
        full_ibi("%s%d" % (config_name,i+1), i, "%s%d%s" % (config_name,i,outdir_suffix), config_name, pressure, script, atom_dir, **args)
        
        p_ave, p_std = lammps_get_pressure(os.path.join(env.localroot,"results","%s%d%s" % (config_name,i,outdir_suffix)), i)
        print "Average pressure is now", p_ave, "after iteration", i, "completed."
        #if(i >= 10 and p_ave < p_std):
        #    if pressure_changed == 0:
        #        pressure = float(pressure)/3.0
        #        pressure_changed = 1
        #        print "(FabMD:) Pressure factor now set to", pressure, "after iteration", i

        #    if abs(p_ave) - (p_std*0.5) < 0: # We have converged, let's not waste further CPU cycles!
        #        print "(FabMD:) Pressure has converged. OPTIMIZATION COMPLETE"
        #        break  

### Utility Functions

def lammps_get_pressure(log_dir,number):
    steps = []
    pressures = []
    LIST_IN = open(os.path.join(log_dir, "new_CG.prod%d.log" % (number)), 'r')
    for line in LIST_IN:
        NewRow = (line.strip()).split()
        if len(NewRow) > 0:
            if NewRow[0] == "Press":
                pressures.append(float(NewRow[2]))
    d1 = np.array(pressures[5:])
    print "READ: new_CG.prod%d.log" % (number)
    return np.average(d1), np.std(d1) #average and stdev

