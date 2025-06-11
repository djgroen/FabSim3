## Introduction

**FabSim3 is an automation toolkit that is normally installed on your local
machine** (e.g. laptop or desktop). It requires a Linux-like environment, and
has been used extensively on e.g. Ubuntu And Mac OS X. If you wish to use
FabSim3 on Windows then we recommend using the Linux Subsystem for Windows.

## Dependencies

1. FabSim3 requires the following Python modules

	* rich
	* fabric2
	* pyyaml
	* pytest
	* pytest-pep8
	* ruamel.yaml
	* numpy
	* beartype

	!!! note
		You **ONLY** need to install [ruamel.yaml](https://pypi.org/project/ruamel.yaml) and  [rich](https://pypi.org/project/rich/)  packages, other packages are installed by FabSim3.
		To install both `ruamel.yaml` and `rich` packages, simply type
		```sh
		pip3 install ruamel.yaml rich
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
	
		export PATH=/path/to/FabSim3/fabsim/bin:$PATH
		export PYTHONPATH=/path/to/FabSim3:$PYTHONPATH

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

## List of available machines and tasks

The basic syntax of any FabSim3 command is the following:
```sh
fabsim <machine_name> <task_name>:<task_argument_list>
```

where

- `task_name` is the name of the task to be executed.

- `task_argument_list` is a comma seperated list of arguments specific to the task.

- `machine_name` is the name of the machine on which the task is to be executed.

You can see the list of available FabSim3 machines by typing:
```sh
fabsim -l machines
```

which gives a table with the `machine_names` and their addresses,

You can see the list of available FabSim3 machines by typing:
```sh
fabsim -l tasks
```

which gives a table with the plugin names and their associated `task_names`.

## OpenMPI Installation for MPI Parallelized Plugins

Some FabSim3 plugins (like **FLEE** and **FACS**) require MPI parallelization. This section explains how to install OpenMPI and configure it for use with FabSim3.

### Why OpenMPI is Needed

MPI (Message Passing Interface) plugins in FabSim3 use `mpirun` commands to execute parallel simulations across multiple cores or nodes. Without OpenMPI, these plugins will fail with errors like:

- `mpirun: command not found`
- `No MPI implementation found`

### Quick Installation (Recommended)

!!! tip "Virtual Environment Recommendation"
    For better dependency management and to avoid conflicts with system packages, it's recommended to install Python packages (including `mpi4py`) within a Python virtual environment. FabSim3's `configure_fabsim.py` script automatically creates a virtual environment in the `VirtualEnv` directory for this purpose.

#### Ubuntu/Debian

Option 1: Ubuntu Package Manager (Recommended for Ubuntu)

```bash
# Install OpenMPI and mpi4py together
sudo apt-get update
sudo apt-get install openmpi-bin openmpi-common libopenmpi-dev python3-mpi4py
```

Option 2: pip (More Universal)

```bash
# Install OpenMPI first
sudo apt-get install openmpi-bin openmpi-common libopenmpi-dev

# Then install mpi4py via pip
pip install mpi4py
```

#### CentOS/RHEL/Fedora

```bash
# CentOS/RHEL
sudo yum install openmpi openmpi-devel

# Fedora
sudo dnf install openmpi openmpi-devel
```

#### macOS

```bash
# Using Homebrew
brew install open-mpi

# Using MacPorts
sudo port install openmpi
```

### Custom Installation from Source (No Admin Privileges Required)

If you need a specific OpenMPI version or custom configuration:

#### 1. Create Installation Directory

```bash
mkdir -p $HOME/opt/openmpi
```

#### 2. Download OpenMPI

```bash
cd $HOME/Downloads
wget https://download.open-mpi.org/release/open-mpi/v4.1/openmpi-4.1.2.tar.gz
tar -xf openmpi-4.1.2.tar.gz
cd openmpi-4.1.2
```

#### 3. Configure and Build

```bash
./configure --prefix=$HOME/opt/openmpi
make all && make install
```

#### 4. Update Environment Variables

Add to your `~/.bashrc`, `~/.bash_profile`, or `~/.zshrc`:

```bash
export PATH=$HOME/opt/openmpi/bin:$PATH
export LD_LIBRARY_PATH=$HOME/opt/openmpi/lib:$LD_LIBRARY_PATH
export CC=$HOME/opt/openmpi/bin/mpicc
export CXX=$HOME/opt/openmpi/bin/mpicxx
```

#### 5. Reload Shell Configuration

```bash
source ~/.bashrc  # or ~/.bash_profile or ~/.zshrc
```

### Installing Python MPI Support

Many FabSim3 MPI plugins also require Python MPI bindings:

```bash
pip install mpi4py
```

!!! note
    If you installed OpenMPI from source, make sure your environment variables are set correctly before installing `mpi4py`, as it needs to find the MPI compiler wrappers.

### Verification

Test your OpenMPI installation:

#### 1. Check OpenMPI Installation

```bash
mpirun --version
which mpirun
```

Expected output:

```bash
mpirun (Open MPI) 4.1.2
/usr/bin/mpirun  # or your custom path
```

#### 2. Test MPI Functionality

```bash
mpirun -np 4 echo "Hello from MPI process"
```

Expected output:

```bash
Hello from MPI process
Hello from MPI process
Hello from MPI process
Hello from MPI process
```

#### 3. Test Python MPI4Py (if installed)

```bash
mpirun -np 2 python -c "from mpi4py import MPI; print(f'Rank {MPI.COMM_WORLD.Get_rank()} of {MPI.COMM_WORLD.Get_size()}')"
```

Expected output:

```bash
Rank 0 of 2
Rank 1 of 2
```

Update your `machines_user.yml` to use system MPI:

```yaml
<machine>
  run_command: "mpirun -n $cores" # or the full path to mpirun (e.g., /usr/bin/mpirun) 
```

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
  <img src="../images/ssh_macos_error.png" width="400" />
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
