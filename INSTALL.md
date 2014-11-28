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

## Testing FabSim

### LAMMPS testing on the local host

1. Install LAMMPS (see http://lammps.sandia.gov for detailed download and installation instructions).
2. Modify `machines_user.yml` to make the `lammps_exec` variable point to the location of the LAMMPS executable. e.g., `lammps_exec: "/home/james/bin/lmp_serial"`.
3. FabSim contains a trial LAMMPS configuration, so there's no need to download that.
4. (first time use only) Create the required FabSim directory using the following command: `fab localhost setup_fabric_dirs`.
5. Run the LAMMPS test data set using: `fab localhost lammps:lammps_lj_liquid,cores=1,wall_time=1:00:0`.
6. You can find the output of your job in the results directory. By default this will be a subdirectory in `~/FabSim/results`.
