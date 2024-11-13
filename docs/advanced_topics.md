## Creating automation scripts
This document briefly details how user/developers can create their own FabSim3 automation.

#### Overview

* Automation scripts allow user/developers to create their own FabSim3 functionalities. They are usually created and modified within individual plugins.
* Base automation scripts reside within the `FabSim3/fabsim/base` subdirectory. These should normally not be modified, but they can serve as examples to create your own functionalities, or as building blocks to create complex functions.
* Plugin-specific automation scripts reside within the base directory of the respective plugin. The script that will be invoked by default is `<plugin_name>.py`. For larger plugins, various other Python scripts can surely be imported into this main script.

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
	This function first navigates to the `blackbox` subdirectory in the local Fabsim3 installation, and subsequently executes the `$script` in that directory. Also, the freehand use of `args` gives a sequence of parameters etc.

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


* The combination of `#!python **args` in the declaration with `#!python update_environment(args)` at the start of the function allows users to specify arbitrary arguments on the command line, and to have those automatically loaded into the FabSim3 environment.
* `#!python with_config()` loads in input files into FabSim3.
* `#!python execute(put_configs,config)` copies the configuration information to the right directory at the remote resource.
On the last line, LAMMPS is run remotely (shown by `#!python script="lammps"`), and the values of args are passed on to that function as well, overriding the default `wall_time` and `memory` specification on that line if the user has specified those variables explicitly already.

#### Accessing FabSim commands from Python scripts

To launch FabSim3 commands from Python scripts, we have established a basic Python API. This file can be found [here](https://github.com/ScientificComputingCWI/SemesterProgramme-UQ/tree/main/forward_UQ/exercises/EasyVVUQ_FabSim3).

We recommend using this API rather than `#!python os.system()` or `#!python subprocess()` directly, as it will allow us to fix any emerging bugs in future versions for you.

## Create Config Directories


* Configuration information is stored in subdirectories of either `config` or `FabSim3/plugins/<module_name>/configs` (to be implemented).
* One directory should be created for each individual simulation problem type.
* Typically, input file names are standardized using default names, to reduce the number of user-specified arguments on the command line (e.g., `config.xml` for `HemeLB`).
* Examples of LAMMPS are provided in the base installation of FabSim3.

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
Variables are obtained from the following sources:

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
    # Optional example of how to use your created variable
    # to create some parameter syntax for your job.

    test_sim(config, **args)
    # start a fictitious job, with the variable present in your FabSim environment.
```

## Creating Job Submission Templates


* Job submission templates are used to convert FabSim environmental information to batch job scripts which can be submitted to remote resource schedulers.
* Domain-independent templates are stored in `FabSim3/fabsim/deploy/templates`, while domain-specific templates should be stored in `FabSim3/fabsim/deploy/<module_name>/templates`.
* Templates consist of two parts, *Header templates* which are scheduler-specific, and *job execution* templates which are code-specific.
* Normally, one new template needs to be added when adding a new machine definition to FabSim3, regardless of the number of codes used on that machine.
* Also, one new template needs to be added for each new code definition to FabSim3, regardless of the number of machines supported.

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
cd $job_results # change directory to the FabSim result dir. Featured in almost all templates.
$run_prefix     # run preparatory commands, as specified within FabSim.

cp -r $job_config_path/* . # Copy over initial conditions to results directory. Featured in almost all templates.
/usr/bin/env > env.log     # Store local supercomputer environment variables. Featured in almost all templates.
$run_command $lammps_exec $lammps_args < $lammps_input > log.lammps # Generically formulated LAMMPS execution command.
```
The last command will likely depend on how parameters are passed to the target code.

* `$run_command` will be substituted by a job execution command such as `mpirun` or `aprun`.
* Other variables contain code/domain-specific information such as input and output destinations, relevant flags or the location of the executable.


## Setting up multiplexing
This document briefly details how user/developers can set up multiplexing for a specific remote, and reduce the number of times they have to retype passwords.

!!! note
	The example below is given for a specific HPC resource, but one can reuse this approach for other machines by changing the `User`, `Host` and `Hostname` variables in step 1, and the name and `remote:` field of the YML entries in step 3.

#### Step 1

Create a local file named `~/.ssh/config`, or append to it.

In this file, you need the following block
```sh
Host archer2
   User <archer2-username>
   HostName login.archer2.ac.uk
   ControlPath ~/.ssh/controlmasters/%r@%h:%p
   ControlMaster auto
   ControlPersist 30m
```

!!! note
        The duration of ControlPersist can be modified to suit your needs. Note however that shorter durations are more secure.

#### Step 2

Create a directory using `mkdir ~/.ssh/controlmasters`

#### Step 3

Modify your existing `machines_user.yml` file such that it contains the following:

```yml
archer2:
  username: <username>
  remote: archer2
  manual_ssh: true
  project: <project>
  budget: <budget>
```


## SSH password authentication with `sshpass`
If (in addition to a public key which can be set in `~/.ssh/config`) a password is required for SSH authentication,  
set `manual_sshpass: true` in your `machine.yml`.  

Example:
```yml
myMachine:
  remote: myHost # see ~/.ssh/config
  manual_sshpass: true
```
The password may then be provided as an environment variable:
```bash
# Avoid leaking password to ~/.bash_history
read -sr SSHPASS && export SSHPASS
# SSHPASS is automatically used if manual_sshpass is set
fabsim myMachine dummy:dummy_test
```

It is also possible to provide a plain text file containing the password by including `sshpass: 'path/to/password.secret'` in your `machine.yml` instead of providing it as an environment variable.  
Make sure that the password is not readable by other users with `chmod g=-rwx,o=-rwx path/to/password.secret`.  
**NOTE:** This does not provide any real security and the use of this method is highly discouraged!

## OpenVPN
When using machines across different private networks, the corresponding configuration in your `machine.yml` file may provide the required configuration file and optional credentials.  
The same considerations as for the use of a password file for `sshpass` apply here.

Example:
```yml
myMachine:
  openvpn_config: /path/to/config.ovpn
  openvpn_auth_user_pass: /path/to/auth-user-pass
```
The credentials may be provided as environment variables if `openvpn_auth_user_pass` is set to `true`:
```bash
# Avoid leaking credentials to ~/.bash_history
read -sr OPENVPN_AUTH_USER && export OPENVPN_AUTH_USER
read -sr OPENVPN_AUTH_PASS && export OPENVPN_AUTH_PASS
# OPENVPN_AUTH_USER and OPENVPN_AUTH_PASS are used if openvpn_auth_user_pass is set to true
fabsim myMachine dummy:dummy_test
```