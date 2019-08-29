## Run Ensemble Examples

### Fab Dummy Ensemble Job

`fab localhost dummy_ensemble` runs this basic ensemble job.
This command takes the files in the config_files/dummy_ensemble directory and copies them into the localhost result directory as usual, but does this for each file in the SWEEP directory

If you want to specify a specific machine, configuration, directory, wall_time and core count per job, you can do that as follows:
`fab <machine_name> dummy_ensemble:<config, e.g. dummy_test>,wall_time=1:00:00,cores=4`

### Lammps Ensemble Job
This example requires the installation of the FabMD plugin. You can install the plugin using:
`fab localhost install_plugin:FabMD`
Also assumes that you have been able to run the basic FabSim examples described in INSTALL.md, and that you have installed and configured LAMMPS on the target machine.

To run type:`fab localhost lammps_ensemble:lammps_ensemble_example,input_name_in_config=in.lammps`

This is an applied version of the FabDummy example. FabMD looks for a directory called `lammps_ensemble_example` in `config_files`. It then looks for a sweep directory (by default called `SWEEP`) that contains a number of input files to iterate through. All the files in `lammps_ensemble_example` directory and one of the sweep directory files will be copied to the host in separate directories (one for each sweep file) and executed in the normal way. 
`lammps_ensemble` requires `input_name_in_config` to be set on the command line, this is the name that each of the sweep files will be changed to when copied to the host. 

### FabDummy Ensemble Job with Replicas

To run *N* jobs with exactly the same configuration (e.g., to account for stochasticity), just run:
`fab localhost dummy:dummy_test,replicas=N`

You can also combine replicas with ensemble runs, e.g. using:
`fab localhost dummy_ensemble:dummy_test,replicas=N`
