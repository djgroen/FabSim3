# Tutorial for Verification and Validation Patterns

## Ensemble Output Validation (EoV) of Multiscale Migration Prediction Simulations

In this tutorial, we showcase the ensemble output validation pattern. It is a pattern that allows users to execute multiple simulations, and perform a streamlined validation procedure across the results of all these simulations.

Our EoV implementation applies a sample testing function on each directory, and prints the outputs to screen. It then uses an aggregation function to combine all outputs into a compound metric.

As an example application of EoV, we developed a `validate_flee` and a `validate_flee_output` function in FabFlee, which apply the VVP to sets of forced migration simulaitons. The VVP can be applied to one or more simulations, and supports the use of a single input configuration (or conflict situation in the context of these models), as well as a range of different input configurations.

Throughout the tutorial we use the `fabsim` command that will give clearer error reporting when you mistype your instruction (if you have set your paths correctly).

### Ensemble Validation of a single conflict with multiple instances

In this first step, we will demonstrate the use of EoV with a forecast simulation of a conflict in Ethiopia. In the `(FabSim3 Home)/plugins/FabFlee/config_files/ethiopia` directory we created an ensemble of configurations, where each configuration differs in the way that the conflict (hypothetically) progresses. All these configurations can be found in `(FabSim3 Home)/plugins/FabFlee/config_files/ethiopia/SWEEP`.

1.  In general, to execute multiple instances of a single conflict scenario, you'll need to run the `flee_ensemble` function as follows:

```sh
fabsim localhost flee_ensemble:<conflict_name>,simulation_period=<number>
```
or

```sh
fabsim <remote machine name> flee_ensemble:<conflict_name>,simulation_period=<number>
```

!!! note
	Any conflict scenario in the `(FabSim3 Home)/plugins/FabFlee/config_files` run with `flee_ensemble` should contain a `SWEEP` directory with different configurations for each instance. 

For instance, to execute ensemble simulations for the Ethiopia conflict, simply type:

```sh
fabsim localhost flee_ensemble:ethiopia,simulation_period=147
```
or

```sh
fabsim eagle_vecma flee_ensemble:ethiopia,simulation_period=147
```
    
2.  You can then copy back any results from completed runs using:

```sh
fabsim localhost fetch_results
```

To check the executed output directory, simply run:

```sh
cd (FabSim3 Home)/results
ls
```

In `(FabSim3 Home)/results`, an output directory for a conflict scenario should be present from previous execution, which is most likely called `<conflict name>_localhost_16` or `<conflict name>_<remote machine name>_<number>` (e.g. ethiopia_localhost_16 or ethiopia_eagle_vecma_4). This conflict output directory should have multiple run directories in `RUNS`. 

3.  To run validation on these output directories of a single conflict with multiple instances, simply go to the `(FabSim3 Home)/plugin/FabFlee` directory and run:

```sh
fabsim localhost validate_flee_output:<conflict name>_localhost_16 
```
or

```sh
fabsim <remote machine name> validate_flee_output:<conflict name>_<remote machine name>_<number of cores used> 
```
    
For instance, to validate the Ethiopia conflict instance, simply type:
   
```sh
fabsim localhost validate_flee_output:ethiopia_localhost_16
```
or

```sh
fabsim eagle_vecma validate_flee_output:ethiopia_eagle_vecma_4 
```
    
You should then see output similar to the picture below:
<figure>
   <img src="../images/vvp3-example.png" width="500"> 
</figure>

Here, the mean score indicates the averaged relative difference between the camp arrival numbers in the simulation versus those observed by UNHCR. The average is performed across all simulations in the ensemble. A value of 1.0 indicates that the forecast is 50% wrong, while a value of 0.0 indicates that the forecast is entirely correct.

### Ensemble Validation of a single conflict instance with replicas

Like many other simulation codes out there, Flee is a non-deterministic code which means that results can vary from run to run. To help account for the uncertainty introduced by non-deterministic elements in the code, we can runs multiple identical copies (or *replicas*) of each individual simulation in our ensemble. Doing so is fairly straightforward, and you can do it as follows:

1.  To run simulations by specifying multiple replicas, you can use a function in this format:

```sh
fabsim localhost flee:<conflict_name>,simulation_period=<number>,replicas=<number>
```
or 

```sh
fabsim <remote machine name> flee:<conflict_name>,simulation_period=<number>,replicas=<number>
```

For instance, to execute an ensemble simulations for the Mali conflict with two replicase, you can type:

```sh
fabsim localhost flee:mali,simulation_period=300,replicas=2
```
or

```sh
fabsim eagle_vecma flee:mali,simulation_period=300,replicas=2
```
    
2.  Next, copy back any results from completed runs using:

```sh
fabsim localhost fetch_results
```

This will copy the output directory of a conflict instance with multiple replicas to `(FabSim3 Home)/results`, which are most likely called `<conflict name>_localhost_16_replica_<number>` or `<conflict name>_<remote machine name>_<number>_replica_<number>` (e.g. `mali_localhost_16_replica_1` or `mali_eagle_vecma_4_replica_2`). 
    
3.  To run an ensemble validation for these replica instances, make a directory with subdirectory `<conflict_name>/RUNS` in `(FabSim3 Home)/results` and place replica runs inside. This will provide average over all those replicas for each conflict instance. 
    
    For instance, there are `mali_localhost_16_replica_1` and `mali_localhost_16_replica_2` output directories, which are placed inside `mali/RUNS` for ensemble validation.
    
4.  To run validation on these output directories of a single instance with replica instances, simply go to the FabFlee directory and run

```sh
fabsim localhost validate_flee_output:<conflict name>
```
or
  
```sh
fabsim <remote machine name> validate_flee_output:<results_directory_name>
```
    
For instance, to validate your Mali conflict instance run on localhost, simply type

```sh
fabsim localhost validate_flee_output:validation_localhost_4
```
or

```sh
fabsim localhost validate_flee_output:validation_eagle_4
    

### Ensemble Validation of multiple conflict instances

To execute multiple conflict scenarios, simply run the `validate_flee` function as follows

```sh
fabsim localhost validate_flee
```
or 

```sh
fabsim <remote machine name> validate_flee
```
which executes multiple simulations in `(FabSim3 Home)/plugins/FabFlee/config_files/validation/SWEEP` containing `burundi2015`, `car2013` and other conflict instances.
    
After simulations are completed, validation values of these conflict instances are calculated and printed to the terminal screen. 

