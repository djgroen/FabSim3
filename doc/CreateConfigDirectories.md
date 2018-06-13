# Create Config Directories
This short document described how to best organize configuration information for FabSim jobs.

## Overview
* Configuration information is stored in subdirectories of either ```config``` or ```plugins/<module_name>/configs``` (to be implemented). 
* One directory should be created for each individual simulation problem type.
* Typically, input file names are standardized using default names, to reduce the number of user-specified arguments on the command line (e.g., config.xml for HemeLB).
* Examples for LAMMPS are provided in the base installation of FabSim3.
