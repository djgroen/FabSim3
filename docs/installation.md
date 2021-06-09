## Dependencies

1. FabSim3 requires the following Python modules

	* fabric3==1.13.1.post1
	* PyYAML
	* numpy
	* ruamel.yaml
	* rich

	!!! note
		You **ONLY** need to install [ruamel.yaml](https://pypi.org/project/ruamel.yaml) package, other packages are installed by FabSim3.
		To install ruamel.yaml package, simply type
		```sh
		pip3 install ruamel.yaml
		```

2. To perform the `Pytest` tests (not required for using FabSim3, but essential for running the tests), you will need [`pytest`](https://docs.pytest.org/en/latest/getting-started.html) and [`pytest-pep8`](https://pypi.org/project/pytest-pep8).

3. To install FabSim3 plugins, [git](https://git-scm.com/) needs to be installed in your machine.


## Installing FabSim3

1. Clone FabSim3 from the GitHub repository:
	```sh
	git clone https://github.com/djgroen/FabSim3.git
	```
2. To install **all** packages automatically and configure yml files, please go to your `FabSim3` directory, and type
	```sh
	python3 configure_fabsim.py
	```

3. After installation process, the root FabSim3 directory should be added to both `PATH` and `PYTHONPATH` environment variables. The instruction to do that will be shown at the end of output of `python3 configure_fabsim.py` command.
	```bash
	Congratulation 🍻
	FabSim3 installation was successful ✔
	
	In order to use fabsim command anywhere in your PC, you need to update the PATH
	and PYTHONPATH environmental variables.
	
		export PATH=/home/hamid/FabSim3/fabsim/bin:$PATH
		export PYTHONPATH=/home/hamid/FabSim3:$PYTHONPATH

		export PATH=~/.local/bin:$PATH
	
	The last list is added because the required packages are installed with flag 
	"--user" which makes pip install packages in your your home instead instead 
	of system directory.


	Tip: To make these updates permanent, you can add the following command at the 
	end of your bash shell script which could be one of ['~/.bashrc', '~/.bash_profile', 
	'~/.zshrc', '~/.bash_aliases'] files, depends on your OS System.

	🛎 To load the new updates in PATH and PYTHONPATH you need to reload your bash shell 
	script, e.g., source ~/.bashrc, or lunch a new terminal.
	```

4. To make the fabsim command available in your system, please restart the shell by opening a new terminal or just re-load your bash profile by `source` command.


## Updating FabSim3

If you have already installed FabSim3 and want to update to the latest version, simply type `git pull` in your local FabSim3 directory.

!!! attention
		Your personal settings like the `machines_user.yml` will be unchanged by `git pull`, **unless** you run `python3 configure_fabsim.py` again, which overwrites the current `machines_user.yml` file.

## Known Issues

Here is the list of known issue that reported by our users so far:

### ssh: connect to host localhost port 22: Connection refused

#### Linux
This is a common issue on Linux system, and it will be solved by re-installing openssh server, to do that

1. Remove SSH with the following command
	```sh
	sudo apt-get remove openssh-client openssh-server
	```
2. Install SSH again with
	```sh
	sudo apt-get install openssh-client openssh-server
	```

#### MacOS
on Mac OSX, make sure turn on **Remote Login** under **System Preferences** then **File Sharing**.

<figure>
  <img src="images/ssh_macos_error.png" width="400" />
</figure>

The easiest way to test FabSim3 is to simply go to the base directory of your FabSim3 installation and try the command demonstrated below in the **List of available commands**.

Mac users may get a `ssh: connect to host localhost port 22: Connection refused` error. This means you must enable remote login. This is done in *System Preferences > Sharing > Remote Login*.

#### FileNotFoundError: [Errno 2] No such file or directory: ‘fab’: ‘fab’

It is possible that your python bin path directory is not in the system `PATH`. You may see a `WARNING` message during the FabSim3 installation (by executing `python3 configure_fabsim.py` command). Here an example :

```bash
  WARNING: The script fab is installed in '<---->/Python/3.<xxx>/bin' which is not on PATH.
  Consider adding this directory to PATH or,
  if you prefer to suppress this warning, use --no-warn-script-location.

  Traceback (most recent call last):
  File "configure_fabsim.py", line 189, in <module>
    main()
  File "configure_fabsim.py", line 148, in main
    cwd=FS3_env.FabSim3_PATH) == 0
  File "<---->/python3..<xxx>/subprocess.py", line 339, in call
    with Popen(*popenargs, **kwargs) as p:
  File "<---->/python3..<xxx>/subprocess.py", line 800, in __init__
    restore_signals, start_new_session)
  File "<---->/python3..<xxx>/subprocess.py", line 1551, in _execute_child
    raise child_exception_type(errno_num, err_msg, err_filename)
FileNotFoundError: [Errno 2] No such file or directory: 'fab': 'fab'	
```

To fix this issue, you need to add the executable path of `fab` to your system `PATH` environment variable. To make this update permanent, please go to your bash file, which could be `~/.bash_profile`, `~/.bashrc`, or `~/.zshrc` depends on your OS and shell version, and add the following line at the end:
	```bash
	export PATH=$PATH:<fab_executable_PATH>
	```

Please make sure that you used the same executable path for `fab` as it mentioned in the warning message.

!!! note
	If you are having a problem which is not listed here, please raise a [github issue](https://github.com/djgroen/FabSim3/issues/new/choose) in FabSim3 repository, and provide a full output log, so we can have a look and provide a solution or address your issue.


### List of available commands

You can see the list of available FabSim3 commands, by simply typing:
	```sh
	fabsim -l
	```
