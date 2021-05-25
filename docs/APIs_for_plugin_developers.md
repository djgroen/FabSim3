
The scope of this document is to provide useful description of commonly used APIs to develop a FabSim3 pluing.

All our APIs, are available on the [FabSim3](https://github.com/djgroen/FabSim3) GitHub repository, and regularly updated. For any further assistance or inquiries, email us at <djgroennl@gmail.com> or <hamid.arabnejad@gmail.com>.

### machine-specific configuration for plugin

Simulations can be run locally, or remotely on HPC resources. The submission and execution process of a workflow requires some information of the target host machine, such as username and host ip address. We encapsulate all these information in form of a human readable structure,YAML language, in two main files:

* `FabSim3/fabsim/deploy/machines.yml` file where general machine-specific configurations are stored, and
* `FabSim3/fabsim/deploy/machines_user.yml` file which contains user-specific information for each remote machine.

In addition to these two files, you can also define machine configuration, for each remote machine, specified for your plugin. This give you better *flexibility* to share your FabSim3 plugin with other research groups. The structure is similar to `machines.yml` and `machines_user.yml` files. But, the file name **should** follow the following pattern :
```sh
machines_<plugin_name>_user.yml
```

Here are two examples of machine-specific configuration : [Example1](https://github.com/djgroen/FabFlee/blob/master/machines_FabFlee_user.yml) , [Example2](https://github.com/djgroen/FabCovid19/blob/master/machines_FabCovid19_user.yml)

#### Usage:
To load machine-specific configuration specified by the user for the input `plugin_name`, you need to wrap the task functions with `#!python @load_plugin_env_vars(plugin_name`)
```python
...
@task
@load_plugin_env_vars(plugin_name)
def <function_name>(input_args):
    ...
...
```
!!! hint
	The `#!python @task` is pre-defined decorator by fabric library which makes your function callable from command line. For more details, please look at [task definition](https://docs.fabfile.org/en/1.12.1/usage/tasks.html#the-task-decorator) in fabric library.
!!! note
	This only works if the machine-specific configuration file (i.e., `machines_<plugin_name>_user.yml`) exists in your plugin directory (i.e., `FabSim3/plugins/<plugin_name>`).

### Common APIs:

#### **`add_local_paths(plugin_name)`**
This function adds your plugin directory to FabSim3 (a) templates and (b) config_files PATH system. FabSim3 uses the templates PATH to find the target script and generates the required script for job execution. The config_path will be use to find your application and transfer the required files/folder to remote machine.

!!! attention
	You should add `add_local_paths` function at top of the main fabric file for your plugin. Otherwise, the target script and application config files for job submission and execution can not be found by FabSim3.

#### **`update_environment(args)`**	
This function updates the environmental variables that are loaded from machine-specific configurations yaml files. The hierarchy for loading machine-specific configurations are:

1. `FabSim3/fabsim/deploy/machines.yml`
2. `FabSim3/fabsim/deploy/machines_user.yml`
3. `FabSim3/plugin/<plugin_name>/machines_<plugin_name>_user.yml` *(if exists)*
4. user input arguments via command line (Modified/Added by `update_environment` function or manual coding)

#### **`with_config(config_name)`**	
This function augments environment variable, such as the remote location variables where the config files for the job should be found or stored, with information regarding a particular configuration name.

#### **`put_configs(config_name)`**	
This function transfers config files to the target machine (local and remote resource). It should be called within the fabric [execute](https://docs.fabfile.org/en/1.14/api/core/tasks.html#fabric.tasks.execute) function to honor host decorators, as follow:

* `#!python execute(put_configs, config_name)` where config_name is the name of the config folder.

#### **`job(args)`**
This is an internal low level job launcher. It will submit a single job to the target machine (local and remote resource). All required parameters for the job are determined from the prepared fabric environment.

#### **`run_ensemble(config, sweep_dir,sweep_on_remote=False, execute_put_configs=True, **args)`**
This function maps and submit an ensemble job to the target machine. For each listed directory from sweep folder, an individual job will be submitted. The input arguments are:


* `config` : the input config folder name
* `sweep_dir` : the PATH to the sweep directory
* `sweep_on_remote` (optional) : this flag indicates if you sweep directory located on your local machine or is saved on remote machine. By default is `#!python False`.
* `execute_put_configs` (optional) : this flag transfers all config files to the remote machine. In case of having config files on the remote machine, this arguments should be set to `#!python False`, to avoid overwriting config files.

#### **`find_config_file_path(config_name)`**
Returns the PATH of input config_name in your plugin.

#### **`get_plugin_path(plugin_name)`**
Returns the local base PATH of input plugin name.

#### **`local(command)`**
Runs the input command on the local system.

#### **`run(command)`**
Runs a shell command on a remote host with following conditions:

* if `#!yaml manual_gsissh` env variable is set to `#!python True` in `fabsim/deploy/machines.yml` file, then the [`gsissh`](https://linux.die.net/man/1/gsissh) command will invoke for execution. The `gsissh` command provides a secure remote login service with forwarding of X.509 proxy credentials.
* if `#!yaml manual_ssh` env variable is set to `#!python True` in `fabsim/deploy/machines.yml` file, the port number from `machines.yml` will be used to establish the ssh connection.
* otherwise, the shell command on a remote system via SSH with default port number `22` will executed.

