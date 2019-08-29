# Create automation scripts.
This document briefly details how user/developers can create their own FabSim automations.

## Overview 
* Automation scripts allow user/developers to create their own FabSim functionalities. They are usually created and modified within individual plugins.
* Base automation scripts reside within the ```base/``` subdirectory. These should normally not be modified, but they can serve as examples to create your own functionalities, or as building blocks to create complex functions.
* Plugin-specific automation scripts reside within the base directory of the respective plugin. The script that will be invoked by default is ```<plugin_name>.py```. For larger plugins, various other Python scripts can of course be imported in this main script.

## How to write automation functions
* All automation functions are written using Python 3.
* On top of that, they rely on shorthand functionalities as provided by Fabric. See for example here for documentation: http://docs.fabfile.org/en/1.14/usage/tasks.html
* Commands to be run on the local client side are called using ```local()```.
* Commands to be run remotely are called using ```run()```.

## Examples

For example, to access a remote resource and scan available modules for a specific name one could write:
```
@task
def probe(label="undefined"):
    """ Scans a remote site for the presence of certain software. """
return run("module avail 2>&1 | grep %s" % label)
```
This task can then be invoked on the archer supercomputer to search for LAMMPS modules by using ```fab archer probe:label=lammps```.

To run an arbitrary bash script locally one could write:
```
@task
def blackbox(script='test.sh', args=''):
    """ black-box script execution. """
    for p in env.local_blackbox_path:
        script_file_path = os.path.join(p, script)
        if os.path.exists(os.path.dirname(script_file_path)):
            local("%s %s" % (script_file_path, args))
return
```
* This function first navigates to the ```blackbox/``` subdirectory in the local Fabsim3 installation, and subsequently executes the $script in that directory.
* Note here the freehand use of ```args```, which can be given a sequence of parameters etc.


To run LAMMPS on a remote host (part of FabMD) one could write:
```
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
    update_environment(args)
    with_config(config)
    execute(put_configs,config)
    job(dict(script='lammps', wall_time='0:15:0', memory='2G'),args)
```
* The combination of ```**args``` in the declaration with ```update_environment(args)``` at the start of the function allows users to specify arbitrary arguments on the command line, and to have those automatically loaded in to the FabSim3 environment.
* ```with_config()``` loads in input files into FabSim3.
* ```execute(put_configs,config)``` copies the configuration information to the right directory at the remote resource.
* On the last line, LAMMPS is run remotely (shown by ```script='lammps'), and the values of ```args``` are passed on to that function as well, overriding the default wall_time and memory specification on that line if the user has specified those variables explicitly already.

## Accessing FabSim commands from Python scripts.

To launch FabSim3 commands from Python scripts, we have established a basic Python API. This file can be found here:
https://github.com/djgroen/FabSim3/blob/master/lib/fabsim3_cmd_api.py

We recommend using this API rather than `os.system()` or `subprocess()` directly, as it will allow us to fix any emerging bugs in future versions for you.
