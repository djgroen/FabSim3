### Create automation scripts
This document briefly details how user/developers can create their own FabSim3 automations.

#### Overview


* Automation scripts allow user/developers to create their own FabSim3 functionalities. They are usually created and modified within individual plugins.
* Base automation scripts reside within the `FabSim3/fabsim/base` subdirectory. These should normally not be modified, but they can serve as examples to create your own functionalities, or as building blocks to create complex functions.
Plugin-specific automation scripts reside within the base directory of the respective plugin. The script that will be invoked by default is `<plugin_name>.py`. For larger plugins, various other Python scripts can of course be imported in this main script.

#### How to write automation functions

* All automation functions are written using Python 3.
* On top of that, they rely on shorthand functionalities as provided by Fabric3. See [documentation](http://docs.fabfile.org/en/1.14/usage/tasks.html) for more information.
* Commands to be run on the local client side are called using `#!python local()`.
* Commands to be run remotely are called using `#!python run()`.

#### Examples
To access a remote resource and scan available modules for a specific name one could write:
```python
@task
def probe(label="undefined"):
  """
  Scans a remote site for the presence of certain software.
  """
  return run("module avail 2>&1 | grep {}".format(label))
```
This task can then be invoked on the archer supercomputer to search for LAMMPS modules by using
```sh
fab archer probe:label=lammps
```
To run an arbitrary bash script locally one could write:
```python
@task
def blackbox(script="test.sh", args=""):
    """
    Black-box script execution.
    """
    for p in env.local_blackbox_path:
        script_file_path = os.path.join(p, script)
        if os.path.exists(os.path.dirname(script_file_path)):
            local("{} {}".format(script_file_path, args))
return
```

!!! note
	This function first navigates to the `blackbox` subdirectory in the local Fabsim3 installation, and subsequently executes the `$script` in that directory. Also, the freehand use of `args` give a sequence of parameters etc.

To run LAMMPS on a remote host (part of FabMD) one could write:
```python
@task
def lammps(config,**args):
    """
    Submit a LAMMPS job to the remote queue.
    The job results will be stored with a name pattern as defined in the environment.
    config : config directory to use to define geometry, e.g. config=cylinder
    Keyword arguments:
            cores : number of compute cores to request
            wall_time : wall-time job limit
            memory : memory per node
    """
    update_environment(args)
    with_config(config)
    execute(put_configs,config)
    job(dict(script='lammps', wall_time='0:15:0', memory='2G'),args)
```


* The combination of `#!python **args` in the declaration with `#!python update_environment(args)` at the start of the function allows users to specify arbitrary arguments on the command line, and to have those automatically loaded in to the FabSim3 environment.
* `#!python with_config()` loads in input files into FabSim3.
* `#!python execute(put_configs,config)` copies the configuration information to the right directory at the remote resource.
On the last line, LAMMPS is run remotely (shown by `#!python script="lammps"`), and the values of args are passed on to that function as well, overriding the default `wall_time` and `memory` specification on that line if the user has specified those variables explicitly already.

#### Accessing FabSim commands from Python scripts

To launch FabSim3 commands from Python scripts, we have established a basic Python API. This file can be found [here](https://github.com/djgroen/FabSim3/blob/master/lib/fabsim3_cmd_api.py).

We recommend using this API rather than `#!python os.system()` or `#!python subprocess()` directly, as it will allow us to fix any emerging bugs in future versions for you.

### Create Config Directories


* Configuration information is stored in subdirectories of either `config` or `FabSim3/plugins/<module_name>/configs` (to be implemented).
* One directory should be created for each individual simulation problem type.
* Typically, input file names are standardized using default names, to reduce the number of user-specified arguments on the command line (e.g., `config.xml` for `HemeLB`).
* Examples for LAMMPS are provided in the base installation of FabSim3.

### FabSim variables
FabSim variables are represented in three different ways:

* in `.yml` files as a key-value pair, e.g.:
```yaml
number_of_cores: 16
```
* within the FabSim Python environment as a member of the env dictionary, e.g.:	
```python
env.number_of_cores = 16
or
update_environment({"number_of_cores":16})
```

* within templates as a `$` denominated variable, which is to be substituted.

#### How variables are obtained or introduced:
Variable are obtained from the following sources:

* Parsed from `.yml` files such as `machines.yml` and `machines_user.yml`, which are loaded on startup.
* Explicitly written/created in the Python code environment. This should be implemented such that the third method will still override this method.
* Overridden or introduced using command-line arguments.

#### How variables are applied

* Directly, by reading values from `#!python env.<variable_name>` in the Python code base.
* Through template substitution, where instances of `$<variable_name>` are replaced with `<variable_value>` in the substitution output.

##### Example of applying a variable
```python
@task
def test_sim(config,**args):
    """
    Submit a my_sim job to the remote queue.
    """

    env.test_var = 300.0 # test variable is set to a default value in the FabSim environment.
    # This will override any defaults set in other parts of FabSim (e.g. machines_user.yml)

    update_environment(args)
    # If a value for test_var is given as a command-line argument,
    # then the default set above will be overridden.

    env.sim_args = "-test-var=%s" % (env.test_var)
    # Optional example how to use your created variable
    # to create some parameter syntax for your job.

    test_sim(config, **args)
    # start a fictitious job, with the variable present in your FabSim environment.
```

### Creating Job Submission Templates


* Job submission templates are used to convert FabSim environmental information to batch job scripts which can be submitted to remote resource schedulers.
* Domain-independent templates are stored in `FabSim3/fabsim/deploy/templates`, while domain-specific templates should be stored in `FabSim3/fabsim/deploy/<module_name>/templates`.
* Templates consist of two parts, *Header templates* which are scheduler-specific, and *job execution* templates which are code-specific.
* Normally, one new template needs to be added when adding a new machine definition to FabSim3, regardless of the number of codes used on that machine.
* Also one new template needs to be added for each new code definition to FabSim3, regardless of the number of machines supported.

#### Header templates

Header templates are usually created as follows:

* Take a batch script header example from the user guide of the respective resource.
* Any existing variable denoted with `$name` should normally be replaced with `$$name` (to prevent substitution with FabSim variables).
* Any hard-coded value should be replaced with a FabSim environment variable name, prefixed with a `$` symbol.
* One then needs to ensure that the respective variables are properly created in FabSim3, e.g. by adding default definitions for them to `machines.yml` if necessary.

##### Example
The example below is the batch header template for the SuperMUC supercomputer.
```sh
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

* Here, `#@ output = job$$(jobid).out` will become `#@ output = job$(jobid).out` after templating, preserving the supercomputer-specific environment variable.
* However, `#@ node = $nodes` will for example become `#@ node = 16` if the `env.nodes` value within FabSim3 equals to `16`.
* Note also that the (MPI) execution command should not reside in this template, as this is supplied separately.

#### Job execution templates
Job execution templates are typically straightforward in their structure, and usually contain just a few preparation commands and a generic MPI job execution formulation.

Here is an example job execution template for the LAMMPS code:
```bash
cd $job_results # change directory to the FabSim results dir. Featured in almost all templates.
$run_prefix     # run preparatory commands, as specified within FabSim.

cp -r $job_config_path/* . # Copy over initial conditions to results directory. Featured in almost all templates.
/usr/bin/env > env.log     # Store local supercomputer environment variables. Featured in almost all templates.
$run_command $lammps_exec $lammps_args < $lammps_input > log.lammps # Generically formulated LAMMPS execution command.
```
The last command will likely depend on how parameters are passed to the target code.

* `$run_command` will be substituted by a job execution command such as `mpirun` or `aprun`.
* other variables contain code/domain-specific information such as input and output destinations, relevant flags or the location of the executable.

