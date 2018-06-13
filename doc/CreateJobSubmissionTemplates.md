# Creating Job Submission Templates
This document explains how users and developers can create new job submission templates.

## Overview
* Job submission templates are used to convert FabSim environmental information to batch job scripts 
which can be submitted to remote resource schedulers*.
* Domain-independent templates are stored in deploy/templates, while domain-specific templates should be stored in deploy/<module_name>/templates.
* Templates consist of two parts, _Header templates_ which are scheduler-specific, and _job execution_ templates which are code-specific. 
* Normally, one new template needs to be added when adding a new machine definition to FabSim3, regardless of the number of codes used on that machine.
* Also one new template needs to be added for each new code definition to FabSim3, regardless of the number of machines supported.

## Header templates

Header templates are usually created as follows: 
1. Take a batch script header example from the user guide of the respective resource.
2. Any existing variable denoted with $name should normally be replaced with $$name (to prevent substitution with FabSim variables).
3. Any hard-coded value should be replaced with a FabSim environment variable name, prefixed with a $ symbol.
4. One then needs to ensure that the respective variables are properly created in FabSim3, e.g. by adding default definitions for them to machines.yml if necessary.

### Example
The example below is the batch header template for the SuperMUC supercomputer.

```
#!/bin/bash
## 
## Copyright (C) University College London, 2007-2012, all rights reserved.
## 
## This file is part of HemeLB and is CONFIDENTIAL. You may not work 
## with, install, use, duplicate, modify, redistribute or share this
## file, or any part thereof, other than as allowed by any agreement
## specifically made by you with University College London.
###
## optional: energy policy tags
##
# DO NOT USE environment = COPY_ALL

#@ job_name = $job_name_template_sh
#@ job_type = $job_type
#@ output = job$$(jobid).out
#@ error = job$$(jobid).err
#@ class = $job_class
#@ tasks_per_node = $corespernode
#@ island_count = $island_count
#@ node = $nodes
#@ wall_clock_limit = $wall_time
#@ network.MPI = sn_all,shared,us
#@ notification = never
#@ initialdir = .
#@ node_usage = shared
#@ queue


# setup modules
. /etc/profile
. /etc/profile.d/modules.sh
```

* Here, ```#@ output = job$$(jobid).out``` will become ```#@ output = job$(jobid).out``` after templating, preserving the supercomputer-specific environment variable.
* However, ```#@ node = $nodes``` will for example become ```#@ node = 16``` if the env.nodes value within FabSim3 equals to 16.
* Note also that the (MPI) execution command should _not_ reside in this template, as this is supplied separately.

## Job execution templates

Job execution templates are typically straightforward in their structure, and usually contain just a few preparation commands and a generic MPI job execution formulation.

Here is an example job execution template for the LAMMPS code:

```
cd $job_results # change directory to the FabSim results dir. Featured in almost all templates.
$run_prefix     # run preparatory commands, as specified within FabSim.

cp -r $job_config_path/* . # Copy over initial conditions to results directory. Featured in almost all templates.
/usr/bin/env > env.log     # Store local supercomputer environment variables. Featured in almost all templates.
$run_command $lammps_exec $lammps_args < $lammps_input > log.lammps # Generically formulated LAMMPS execution command.
```

The last command will likely depend on how parameters are passed to the target code. 
* $run_command will be substituted by a job execution command such as ```mpirun``` or ```aprun```.
* other variables contain code/domain-specific information such as input and output destinations, relevant flags or the location of the executable.


