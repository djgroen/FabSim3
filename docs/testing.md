# FabSim3 Testing

The easiest way to test FabSim3 is by installing the FabDummy plugin, and to try out its various features.

## FabDummy testing on localhost

### FabDummy Plugin Installation
Open a terminal, and simply type:
```sh
fabsim localhost install_plugin:FabDummy
```
!!! info
	FabDummy plugin will be downloaded under `FabSim3/plugins/FabDummy`.

### Basic Testing
1. To run a dummy job, type:
```sh
fabsim localhost dummy:dummy_test
```
2. To run an ensemble of dummy jobs, type:
```sh
fabsim localhost dummy_ensemble:dummy_test
```
3. For both cases, i.e. a single dummy job or an ensemble of dummy jobs, you can fetch the results by using:
```sh
fabsim localhost fetch_results
```

### Intermediate Testing

#### Executing an ensemble job on a remote host

1. Ensure the host is defined in machines.yml, and the user login information in `deploy/machines_user.yml`.
2. To run a dummy job, type `fabsim <machine name> dummy_ensemble:dummy_test`. This does the following:
  a. Copy your job input, which is in `plugins/FabDummy/config_files/dummy_test`, to the remote location specified in the variable `remote_path_template` in `deploy/machines.yml` (not it will substitute in machine-specific variables provided in the same file).
  b. Copy the input to the remote results directory.
  c. Substitute in the first input file in `plugins/FabDummy/config_files/dummy_test/SWEEP`, renaming it in-place to dummy.txt for the first ensemble run.
  d. Start the remote job.
  e. Repeat b-d for each other base-level file or directory in `plugins/FabDummy/config_files/dummy_test/SWEEP`.
3. Use `fabsim <machine> job_stat` to track the submission status of your jobs, or `fabsim <machine> monitor` to poll periodically for the job status.
4. If the stat or monitor commands do not show any jobs being listed, then all your job has finished (successfully or unsuccessfully).
5. You can then fetch the remote data using `fabsim localhost fetch_results`, and investigate the output as you see fit. Local results are typically locations in the various `results/` subdirectories.

#### Executing an ensemble job on a remote host with replicas

Replicas are jobs that have identical inputs and configurations. Their outputs may be different however, e.g. due to stochastic or non-deterministic aspects of the simulation algorithm. To run each instance of the ensembles with *N* replicated instances, add a `replicas=<N>` to your command. For example, to run a dummy ensemble with 5 replicas each, just use `fabsim <machine name> dummy_ensemble:dummy_test,replicas=5`.

#### Using a VECMA Verification and Validation Pattern (VVP) to compare two code versions

FabDummy contains a minimal demonstrator script of VECMA VVP 2, which compares a candidate code version output with that of a stable intermediate form. You can run this little demonstrator by typing:

`fabsim localhost dummy_sif:dummy_test`

### Advanced Testing

#### Executing an ensemble job with QCG-PilotJob on a remote host

1. Ensure you are able to perform the first and second intermediate test.
2. Ensure that you have QCG-PilotJob installed on the remote machine.
3. 
```sh
fabsim <machine_name> dummy_ensemble:dummy_test,replicas=5,PJ=true,cores=1,PJ_size=2
```

Here, `cores` indicates the number of cores used per dummy program, and `PJ_size` indicates the number of **nodes** used by QCG-PilotJob in total.


