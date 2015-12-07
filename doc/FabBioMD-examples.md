### This guide will take you through different FabBioMD functions relevant for Binding Affinity Calculation using BAC protocol (ensemble simulation). There is a standard directory structure for the input/output files which BAC accepts. An example is available in FabSim already. In the following steps you will use that example to run each step of BAC protocol one by one using different FabBioMD functions.

1. Directory restructuring -
The `dir_structure` command is used to restructure the directory structure created originally by BAC Builder so as to adapt it for ensemble simulation. Its usage is as follows:

fab localhost dir_structure:path=$full_path_to_input,num_rep=$number_of_replicas

where `path` is the full path to the input directory and `num_rep` is the number of replicas you want to perform, all of which together constitute the ensemble. The standard is 25 replicas in the BAC protocol. In the current example, path=$local_config_path/bac_example and num_rep=5.

2. Ensemble NAMD job submission -
There are commands specific to machine type for this task. Following is the usage:

fab $machine_name $function_name:$config_name,optional_arguments

where $function_name can be either `bac_namd_archerlike` or `bac_namd_hartreelike` and $machine_name can be `archer` for the former while `bluewonder1` or `bluewonder2` for the latter. There are some optional arguments which you may opt to provide additionally to overwrite their default values, which are `replicas` (number of replicas), `cores` (number of cores), `wall_time` (wall clock time), etc. 

In the current example, you can use which remote host you have access to (or like!), $config_name should be `bac_example` and the additional arguments `replicas=5` and `stages_eq=2` need to be added necessarily. You may also want to provide the number of cores and wall clock time using the arguments `cores` and `wall_time` respectively.

It is important to note here that there is a slight difference between submission on Hartree and ARCHER; when inputting the number of cores, Hartree asks for cores per replica, whereas ARCHER asks for total number of cores for all replicas. The time format is also different between the commands.

3. Free energy calculation submission (when simulation trajectories present on the local machine; this step needs to be ignored in our current example with bac_example)
(NOTE: You need to put your input file for MMPBSA/NMODE calculation in AMBER format named as `nmode.in` in the directory `replicas` in your input folder)
There are commands specific to machine type for this task as well. Following is the usage:

fab $machine_name $function_name:$config_name,optional_arguments

where $function_name can be either `bac_nmode_archerlike` or `bac_nmode_hartreelike` and $machine_name can be `archer` for the former while `bluewonder1` or `bluewonder2` for the latter. There are some optional arguments which you may opt to provide additionally to overwrite their default values, which are `replicas` (number of replicas), `cores` (number of cores), `wall_time` (wall clock time), etc. 

fab  bluewonder1 bac_nm_remote_hartreelike:remote_path=/path/to/remotefile,replicas=$number_of_replicas,cores=$number_of_cores,wall_time=hh:mm:ss

fab archer bac_nm_remote_archerlike:remote_path=/path/to/remotefile,replicas=$number_of_replicas,cores=$number_of_cores,wall_time=hh:mm

4. Free energy calculation submission (when simulation trajectories present on the remote machine)
There are commands specific to machine type for this task as well. Following is the usage:

fab $machine_name $function_name:remote_path=$path_to_input,optional_arguments

where $function_name can be either `bac_nm_remote_archerlike` or `bac_nm_remote_hartreelike` and $machine_name can be `archer` for the former while `bluewonder1` or `bluewonder2` for the latter. `remote_path` is the full path of the directory on remote location containing the input files. There are some optional arguments which you may opt to provide additionally to overwrite their default values, which are `replicas` (number of replicas), `cores` (number of cores), `wall_time` (wall clock time), etc. 

In the current example, $machine_name has to be consistent with the one you used for Step 2 above, $function_name should also be chosen accordingly, remote_path should be the full path (will vary depending on your machine) and give an additional argument `replicas=5`


