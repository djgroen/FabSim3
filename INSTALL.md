Installing and Testing FabSim
======

## Dependencies

### The "pip" way
FabSim requires the following Python modules:
* PyYAML (any version) 
* fabric3 (1.1.13.post1 has worked for us)

You can install using `pip3 install PyYAML` and `pip3 install fabric3`.

To perform the Py.test tests (not required for using FabSim, but essential for running the tests), you will need python3-pytest and python3-pytest-pep8.

### Using apt on Ubuntu (tried with 18.04 Bionic Beaver)
(when using a server version, make sure you add `universe` at the end of the first line of `/etc/apt/sources.list`)
* `sudo apt install python3-yaml`
* `sudo apt install python3-numpy`
* `sudo apt install python3-pip`
* `sudo apt install python3-pytest-pep8` (this will also install py.test for Python3)
* go to the `fabric3_base` subdirectory.
* run `pip3 install Fabric3-1.14.post1-py3-none-any.whl`

### Note for MAC users
For Mac users, you might also need ssh-copy-id. This can be installed using `brew install ssh-copy-id`.



## Installation

1. Clone the code from the GitHub repository.

2. The 'fab' command, which comes with Fabric, needs to be usable directly from the command line. You can make it usable by ensuring that the command resides in your `$PATH` environment.

3. Ensure that the main FabSim3 directory is in your $PYTHONPATH environment variable. An easy way to accomplish this is by adding the following to the end of your $HOME/.bashrc file:
```
export PYTHONPATH=(path of your FabSim3 directory):$PYTHONPATH
```
Note that you may have to restart the shell for this change to apply.

4. Copy `machines_user_example.yml` in the `deploy/` subdirectory to `machines_user.yml`. Modify its contents so that it matches with your local settings. For first (local) testing, one must change the settings under the sections `default:` and `localhost:` so as to update the paths of FabSim directory and lammps executable respectively. 

Note: For Mac Users, be sure to override the default home directory, by switching the `home_path_template` variable by uncommenting the following line: 
```
home_path_template: "/Users/$username
```

5. To enable use of FabSim on your local host, type `fab localhost setup_fabsim`. 

6. To enable use of FabSim on any other remote machine, make sure that (a) machines.yml contains the specific details of the remote machine, and (b) machines_user.yml contains the specific information for your user account and home directory for the machine. After that, simply type 'fab <machine_name> setup_fabsim'.

### Installing plugins

By default, FabSim3 comes with the FabMD plugin installed. Other plugins can be installed, and are listed in deploy/plugins.yml.

To install a specific plugin, simply type: `fab localhost install_plugin:<plug_name>`

To create your own plugin, please refer to doc/CreatingPlugins.md

### Updating 

If you have already installed FabSim and want to update to the latest version, in your local FabSim directory simply type `git pull`. Your personal settings like the `machines_user.yml` will be unchanged by this.

To update plugins you will have to `git pull` from within each plugin directory as and when required.

## Testing FabSim

The easiest way to test FabSim is to simply go to the base directory of your FabSim installation and try the examples below.

Note: Mac users may get a `ssh: connect to host localhost port 22: Connection refused` error. This means you must enable remote login. This is done in `System Preferences > Sharing > Remote Login`.

### List available commands.
1. Simply type `fab localhost help`.

### FabDummy testing on the local host
####  Installation
Simply type `fab localhost install_plugin:FabDummy` anywhere inside your FabSim3 install directory. `FabDummy` plugin will be downloaded under `<fabsim home folder>/plugins/FabDummy` 
####  Testing
1. To run a dummy job, type `fab localhost dummy:dummy_test`
2. To run an ensemble of dummy jobs, type `fab localhost dummy_ensemble`
3. for both cases, i.e., a single dummy job or an ensemble of dummy jobs, you can fetch the results by using `fab localhost fetch_results`

### LAMMPS testing on the local host

1. Install LAMMPS (see http://lammps.sandia.gov for detailed download and installation instructions).
2. Modify `machines_user.yml` to make the `lammps_exec` variable point to the location of the LAMMPS executable. e.g., `lammps_exec: "/home/james/bin/lmp_serial"`.
3. FabSim contains sample LAMMPS input files, so there's no need to download that.
4. (first time use only) Create the required FabSim directory using the following command: `fab localhost setup_fabsim`.
5. Run the LAMMPS test data set using: `fab localhost lammps_dummy:lammps_dummy,cores=1,wall_time=1:00:0`.
6. Run `fab localhost fetch_results` to copy the output of your job in the results directory. By default this will be a subdirectory in `~/FabSim/results`.

### Creating the relevant FabSim directories on a local or remote host

1. Ensure that you have modified `machines_user.yml` to contain correct information for your target machine.
