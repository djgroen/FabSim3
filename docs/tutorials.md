
# Tutorials

For FabSim3, we provide several interactive tutorials, as well as static tutorials.

The interactive tutorials use Jupyter notebooks, and they can be found here: https://github.com/vecma-project/VECMA-tutorials/tree/master/FabSim3

As for the static tutorials, please find them below.

## Creating a new plugin

To create a new plugin for FabSim3:

1. Fork the [FabDummy](https://github.com/djgroen/FabDummy) repository.
2. Rename the repository, and modify it to suit your own needs as you see fit.
3. Rename **`FabDummy.py`** to the **`<name of your plugin>.py`**.
4. In your new plugin repository, at the top of **`<name of your plugin>.py`**, change `#!python add_local_paths("FabDummy")`  `#!python add_local_paths("name of your plugin")`.
5. In the main FabSim3 repository, add an entry for your new plugin in `fabsim/deploy/plugins.yml` file.
6. Set up your plugin using
```sh
fab localhost install_plugin:<name of your plugin>
```
7. You’re good to go, although you’ll inevitably have to debug some of your modifications made in the second step of course.

### Writing a Plugin From scratch

In this tutorial, we explain how to write a FabSim3 plugin from scratch. To keep simplicity, the basic functionalities are presented here, for more advanced and complicated functionalities, we suggest the reader to have a look at the current plugins presented in "plugins" section of this work.


For this tutorial, a simple application, namely *cannon_app*, which calculates the range of a projectile fired at an angle is selected. By using simple physics rules, you can find how far a fired projectile will travel. The source code for this application, written in three of the most widely used languages: C, Java, and Python, is available here : <https://github.com/arabnejad/cannon_app>. The *cannon_app* reads the input parameters from a simple txt file and calculates the distance until ball hits the round. How far the ball travels will depend on the input parameters such as : speed, angle, gravity, and air resistance. Figure below shows the sample input setting file and the generated output plot.

<figure>
   <img src="../images/canonsim_example.png" width="600"> 
</figure>



??? info "cannon_app source codes"

    The source code of *cannon_app* written in three of the most widely used languages: C, Java, and Python can be found in <https://github.com/arabnejad/cannon_app>

    === "cannonsim.py"

        ``` python
        --8<-- "docs/source_codes/cannonsim.py"
        ```

    === "cannonsim.java"

        ``` java
        --8<-- "docs/source_codes/cannonsim.java"
        ```

    === "cannonsim.c"

        ``` c
        --8<-- "docs/source_codes/cannonsim.cpp"
        ```


#### New plugin preparation

To create a new plugin for *cannon_app* application, you need to follow a files and folders structure to be used by FabSim3. To do that, follow these steps:

1. Create a folder, namely `FabCannonsim` under `plugins` directory in your local FabSim3 folder.

2. Create two sub-folders, `config_files` where we put the application there, and `templates` where all template files are placed.

3. Clone or download the *cannon_app* application in the `FabCannonsim/config_files` folder that just created.
	```sh
	cd FabCannonsim/config_files
	git clone https://github.com/arabnejad/cannon_app.git
	```

4. In `FabCannonsim` folder, create two empty files:
	* `FabCannonsim.py`, which contains the plugin source code.
	* `machines_FabCannonsim_user.yml`, which contains the plugin environmental variables.

5. Add a new plugin entry in `plugins.yml` file located in `FabSim3/fabsim/deploy` folder.
	```yaml
	...
	FabCannonsim:
		repository: <empty>
	```


	!!! note
		For now, we left repository with `empty` value. Later, this can be filled by the GitHub repo address of your plugin.


To summarize this part, by following above steps, the file and directory should be as shown in figure below:

<figure>
   <img src="../images/canonsim_structure.png" width="700"> 
</figure>


- (a) demonstrates the directory tree structures
- (b) show the updated `plugins.yml` file located in `FabSim3/fabsim/deploy` folder

!!! attention
	Please note that the folders name highlighted with **red** color in (a) will be used by FabSim3 for job configuration and execution and should not be changed. Also, all three (1) the plugin name, here `FabCannonsim`, (2) the plugin fabric python file, here `FabCannonsim.py`, and (3) the plugin entry in `plugins.yml` file, should be **identical**.

#### Write application-specific functionalities
To call and execute a function from command line, it should be tagged as a Fabric task class. This part of tutorial explains how to write a function/task to execute a single or ensemble jobs of your application.

1. **Single single job execution**

	Code below shows a sample function for single job execution in `FabCannonsim.py`.
	```python
	--8<-- "docs/source_codes/cannonsim_single_job.py"
	```

	The following paragraphs will explain it line by line:

	* `#!python from base.fab import *`

		loads all FabSim3 pre-defined functions.

	* `#!python add_local_paths("FabCannonsim")`
	
		sets the default location for templates, python scripts, and config files.

	* `#!python @task`

		Marks the function, as a callable task, to be executed when it is invoked by `fabsim` from command line.


	* `#!python @load_plugin_env_vars("FabCannonsim")`

		Loads all machine-specific configuration information that is specified by the user for the input plugin name.

		The below code shows the sample machine-specific configuration yaml file for the *cannon_app* application.

		```yaml
		--8<-- "docs/source_codes/machines_FabCannonsim_user.yml"
		```


	* `#!python def Cannonsim(app, **args)`

		Defines the task name. The defined task name can be called from command line alongside `fabsim` command, e.g.,
			```sh
			>_ fabsim <remote/local machine> Cannonsim:<input parameters>
			```

	* `#!python update_environment(args)`

		is a predefined FabSim3 function which updated the environmental variables that are used as a combination settings registry and shared inter-task data namespace. The complete list of FabSim3 environmental variables can be found in `machines.yml` and `machines_user.yml` located in `FabSim3/fabsim/deploy` folder.

	* `#!python with config(args)`

		augments the FabSim3 environment variable, such as the remote location variables where the config files for the job should be found or stored, with information regarding a particular configuration name.

	* `#!python execute(put_configs, app)`

		transfers the config files to the remote machine to be used in launching jobs.

	* `#!python env.script = "cannonsim"`

		the `env.script` variable contains the name of template script file to be used for execution of a job on the target machine, which can be local host or HPC resources. This script will be called when the job execution starts, and contains all steps, such as set environment variable, or commands line to call/execute the application. 

		The below code shows the script file, namely `cannonsim`, for the *cannon_app` application.

		```bash
		--8<-- "docs/source_codes/cannonsim"
		```

		!!! tip
			By default, FabSim3 loads all required scripts from `templates` folder located in `plugin` directory. Hence the `cannonsim` file should be saved in `FabSim3/plugins/FabCannonsim/templates` directory to be used by `fabsim` command for *cannon_app* execution.


		FabSim3 uses a template/variable [substitution](https://docs.python.org/3/library/string.html#template-strings) system to easily generate the required script for executing the job on the target local/remote machine. The used system is `$`-based substitutions, where `$var` will replace the actual value of the variable `var`, and `$$` is an escape and is replaced with a single `$`.

		To demonstrate, you can see the generated sample script for executing the *cannon_app* application on the `localhost` below:

		```sh
		--8<-- "docs/source_codes/cannonsim_localhost_script.sh"
		```


	* `#!python job(args)`

		is an internal low-level job launcher defined in FabSim3. 


	To submit and execute a single *cannon_app* job,
	```sh
	# to execute on localhost
	fabsim localhost Cannonsim:cannon_app
	# to execute on remote machine
	fabsim eagle_vecma Cannonsim:cannon_app
	```

	!!! note
		Please note that, the target machine, e.g., `localhost` or `eagle_vecma`, should be defined and available in both in both `machines.yml` and `machines_user.yml` files. To see the machine configuration attribute, you can run : 
		```sh
		fabsim <target_host> machine_config_info
		```

		Additionally, you can overwrite or add new attributes to the target machine, tailored to your plugin, in `machines_<plugin_name>_user.yml` file.



2. **Ensemble job execution**

	An ensemble-based simulation uses variation in input or output data, model parameters, or available versions
	For the `cannon_app` application, the input `simsetting.txt` file can be varied for different ensemble runs. 
	To set up an ensemble simulation, first we need to create a `SWEEP` folder in the root directory of application. Inside the `SWEEP` folder, each ensemble run should be represented by a different folder name. To vary the input `simsetting.txt` file, we should follow the same relative path of that file inside each run directory in `SWEEP` folder.

	!!! note
		Please note that, by default, FabSim3 builds and constructs the required number of ensembles runs based on a default folder, namely `SWEEP`, located inside the application config directory

	Figure below illustrates sample files and folder structures with 3 ensemble runs.

	<figure>
	   <img src="../images/canonsim_ensemble_structure.png" width="700"> 
	</figure>

	- (a) Sample files and folder structure for cannon app application with 3 ensemble runs. Please note that, the target file, here is `simsetting.txt`, should follow the same path as the original version. 
	- (b) the generated files and folder structure for execution side of the ensemble execution.



	Code below shows the sample function for an ensemble execution in `FabCannonsim.py` file.


	```python
	--8<-- "docs/source_codes/cannonsim_ensemble_job.py"
	```

	Most part of this code is already explained in the previous section, i.e., single job submission. The following paragraphs will explain the required lines for an ensemble functionality:

	* `#!python sweep_dir = find_config_file_path(app) + "/SWEEP"`

		set the `SWEEP` directory `PATH`. As it mentioned earlier, the `SWEEP` directory should be located in the root of the application. The API `find_config_file_path(app)` will return the `PATH` to the application, here, the return value will be : `FabSim3/plugins/FabCannonsim/config_files/cannon_app`.

	* `#!python run_ensemble(app, sweep_dir, **args)`

		is an internal low-level function to map and execute ensemble jobs. Two mandatory input arguments are : (1) the config/application directory name, and (2) the `PATH` to `SWEEP` directory which contains inputs that will vary per ensemble simulation instance.


	As you can see in code above, unlike the single job execution, there is no need to call `execute(put_configs, app)`; The `execute` function will be called automatically by the `run_ensemble` API.


	To submit and execute an ensemble *cannon_app* job,
	```sh
	# to execute on localhost
	fabsim localhost Cannonsim_ensemble:cannon_app
	# to execute on remote machine
	fabsim eagle_vecma Cannonsim_ensemble:cannon_app
	```

## How to use `fabsim` API commands from python code

Within FabSim3, in addition to `fabsim` command APIs, we also provide this functionality to call `fabsim` commands from a python code. The best example that showcases how to do this is FabUQCampaign. The repository for that can be found here: https://github.com/wedeling/FabUQCampaign


## Advanced Plugins Examples

For more advanced examples, please see the plugins available in the `fabsim/deploy/plugins.yml` file. Both [FabFlee](https://github.com/djgroen/FabFlee), and [FabMD](https://github.com/UCL-CCS/FabMD) are good examples that showcase the possibilities of FabSim3.
