## FabMD examples
These examples require the installation of the FabMD plugin. You can install the plugin using:
``fab localhost install_plugin:FabMD''

### Perform an example IBI calculation
This example assumes that you have been able to run the basic FabSim examples described in INSTALL.md, and that you have installed and configured LAMMPS on the target machine.

1. Run ``fab (machine_name) lammps:ibi_example_poly1,wall_time=12:00:00,cores=(number_of_cores)'' 
Here, *number_of_cores* typically equals to the equivalent of one node, e.g. 24 cores for the ARCHER supercomputer)
2. Run ``fab (machine_name) full_ibi_multi:start_iter=1,num_iters=5,config_name=ibi_example_poly1,outdir_suffix=\_(machine_name)_(number_of_cores),cores=(number_of_cores),wall_time=1:00,pressure=1.0'' 
Here, please note that *number_of_cores* should be substituted for a number *twice*.
