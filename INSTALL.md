Installing and Testing FabSim
======

## Dependencies

FabSim requires the following Python modules:
* PyYaml 
* Fabric (version 1.5.3 and 1.10.0 have worked OK for us)

You can install them any way you like. Most people prefer `pip`, although you could also choose to use `easy_install`.

## Installation

1. Clone the code from the GitHub repository.
2. The 'fab' command, which comes with Fabric, needs to be usable directly from the command line. You can make it usable by ensuring that the command resides in your `$PATH` environment.
3. Copy `machines_user_example.yml` in the `deploy/` subdirectory to `machines_user.yml`. Modify its contents so that it matches with your local settings. For first (local) testing, one must change the settings under the sections `default:` and `localhost:` so as to update the paths of FabSim directory and lammps executable respectively.
4. To enable use of FabSim on your local host, type `fab localhost setup_fabsim`. 
5. To enable use of FabSim on any other remote machine, make sure that (a) machines.yml contains the specific details of the remote machine, and (b) machines_user.yml contains the specific information for your user account and home directory for the machine. After that, simply type 'fab <machine_name> setup_fabsim'.

## Testing FabSim

### LAMMPS testing on the local host

1. Install LAMMPS (see http://lammps.sandia.gov for detailed download and installation instructions).
2. Modify `machines_user.yml` to make the `lammps_exec` variable point to the location of the LAMMPS executable. e.g., `lammps_exec: "/home/james/bin/lmp_serial"`.
3. FabSim contains a trial LAMMPS configuration, so there's no need to download that.
4. (first time use only) Create the required FabSim directory using the following command: `fab localhost setup_fabric_dirs`.
5. Run the LAMMPS test data set using: `fab localhost lammps:lammps_lj_liquid,cores=1,wall_time=1:00:0`.
6. You can find the output of your job in the results directory. By default this will be a subdirectory in `~/FabSim/results`.

### FabBioMD testing on the local or remote host

1. Install NAMD (required just for local host).
2. Modify `machines_user.yml` to make the `namd_exec` variable point to the location of the NAMD executable. e.g., `namd_exec: "/home/james/bin/namd/2.9"` (This needs to be done individually for all local or remote hosts).
3. FabSim contains a trial NAMD configuration, so there's no need to download that.
4. Run the NAMD test data set using: `fab machine_name namd:namd_toy_model,cores=x,wall_time=y`, where you can choose the values of x and y depending on your machine.
5. You can find the output of your job in the results directory. By default this will be a subdirectory in `~/FabSim/results`.

### Creating the relevant FabSim directories on a local or remote host

1. Ensure that you have modified `machines_user.yml` to contain correct information for your target machine.
