# FabSim3 Plugins

### Installing plugins

By default, FabSim3 comes with the [FabDummy](https://github.com/djgroen/FabDummy) plugin installed. Other plugins can be installed, and are listed in `fabsim/deploy/plugins.yml` file.

* To install a specific plugin, simply type:
	```sh
	fabsim localhost install_plugin:<plug_name>
	```

* To install plugin from a *specific* github branch, you can use `branch` keyword
	```sh
	fabsim localhost install_plugin:<plug_name>,branch=<branch_name>
	```

### Creating a new plugin

To create a new plugin for FabSim3:

1. Fork the [FabDummy](https://github.com/djgroen/FabDummy) repository.
2. Rename the repository, and modify it to suit your own needs as you see fit.
3. Rename **`FabDummy.py`** to the **`<name of your plugin>.py`**.
4. In your new plugin repository, at the top of the **`<name of your plugin>.py`**, change `#!python add_local_paths("FabDummy")`  `#!python add_local_paths("name of your plugin")`.
5. In the main FabSim3 repository, add an entry for your new plugin in `fabsim/deploy/plugins.yml` file.
6. Set up your plugin using
```sh
fab localhost install_plugin:<name of your plugin>
```
7. You’re good to go, although you’ll inevitably will have to debug some of your modifications made in the second step of course.

### Plugins Examples

For examples, see the plugins available in `fabsim/deploy/plugins.yml` file. [FabDummy](https://github.com/djgroen/FabDummy), [FabFlee](https://github.com/djgroen/FabFlee), and [FabMD](https://github.com/UCL-CCS/FabMD) are particularly good examples to investigate.

### FabDummy testing on the local host

#### FabDummy Plugin Installation
Open a terminal, and simply type:
```sh
fabsim localhost install_plugin:FabDummy
```
!!! info
	FabDummy plugin will be downloaded under `FabSim3/plugins/FabDummy`.

#### Testing
1. To run a dummy job, type:
```sh
fabsim localhost dummy:dummy_test
```
2. To run an ensemble of dummy jobs, type:
```sh
fabsim localhost dummy_ensemble:dummy_test
```
3. for both cases, i.e., a single dummy job or an ensemble of dummy jobs, you can fetch the results by using:
```sh
fabsim localhost fetch_results
```

For more advanced testing features, please refer to the FabDummy tutorial at <https://github.com/djgroen/FabDummy/blob/master/README.md>.

### LAMMPS testing on the local host

#### Dependencies and Pre-Configurations
1. Install LAMMPS (see <http://lammps.sandia.gov>). We suggest to install it from source files.
	* Download the latest stable version from <https://lammps.sandia.gov/tars/lammps-stable.tar.gz>
	* Extract tar file by `tar xvf lammps-stable.tar.gz`. This will create a folder named: *lammps-3Mar20* (The date may change depending of the updates in the website).
	* Before keep going it is necessary to solve some dependencies: build-essential (to compile in C), MPIch (to work in parallel) , FFTW ( to compute long-range interactions), libxaw7 (to compute the movies). In one line code you choose
	```sh
	sudo apt-get install build-essential libxaw7-dev
	```
	* Then, go to the extract folder, and execute following commands
	```sh
	~$ cd lammps-3Mar20
	~/lammps-3Mar20$ cd src/STUBS
	~/lammps-3Mar20/src/STUBS$ make clean
	~/lammps-3Mar20/src/STUBS$ make
	~/lammps-3Mar20/src/STUBS$ cd ..
	~/lammps-3Mar20/src$ make clean-all
	~/lammps-3Mar20/src$ make serial
	```
	* If the installation part worked correctly, you should be able to find `lmp_serial` executable file inside `lammps-3Mar20/src` folder

2. Modify `fabsim/deploy/machines_user.yml` file to make the `lammps_exec` variable point to the location of the LAMMPS executable. e.g.
```yaml
localhost:
        lammps_exec: "/home/james/bin/lmp_serial"
```
3. FabSim3 contains sample LAMMPS input files, so there’s no need to download that.

#### FabMD Plugin Installation
Before run LAMMPS test data set, you should install FabMD which provides functionality to extend FabSim3’s workflow and remote submission capabilities to LAMMPS specific tasks. Please install it by typing:
```sh
fabsim localhost install_plugin:FabMD
```

#### Testing
1. Run the LAMMPS test data set using:
```sh
fabsim localhost lammps_dummy:lammps_dummy,cores=1,wall_time=1:00:0
```
2. Run the following command to copy the output of your job in the results directory. By default this will be a subdirectory in `FabSim3/results`:
```sh
fabsim localhost fetch_results
```