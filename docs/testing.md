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

To run a dummy job, type:

```sh
fabsim localhost dummy:dummy_test
```

To run an ensemble of dummy jobs, type:

```sh
fabsim localhost dummy_ensemble:dummy_test
```

For both cases, i.e. a single dummy job or an ensemble of dummy jobs, you can fetch the results by using:

```sh
fabsim localhost fetch_results
```

### Known Issues

Issue:

```bash
mpirun: command not found
```

Some MacOS users may encounter an error where `mpirun` is not found when running jobs locally on FabSim3. This is often due to the system not locating the correct path for `mpirun`.

Solution:

To resolve this issue, update the `run_command` attribute in `machines_user.yml`. For localhost execution, the attribute typically looks like this:

```yaml
default:
  run_command: mpirun -np $cores
```

However, if mpirun is installed in a custom directory, you need to specify the full path in `machines_user.yml` under the default section. Locate where mpirun is installed on your system, then update the run_command as shown below:

```yaml
default:
  run_command: /path/to/mpirun -np $cores
```

By adding the full path, you avoid the mpirun not found error and enable smoother execution of parallel tasks on your machine.

### Intermediate Testing

#### Running an Ensemble with the SWEEP Directory

The run_ensemble function allows you to manually construct and run an ensemble of jobs using the SWEEP directory. Each subdirectory within SWEEP represents a unique job configuration that will be submitted as part of the ensemble.

Function Overview: run_ensemble

```bash
run_ensemble(
    config,
    sweep_dir,
    sweep_on_remote=False,
    execute_put_configs=True,
    upscale=None,
    replica_start_number=1,
    **args
)
```

#### Parameter Descriptions

- **config**: The base configuration folder or file name used for the ensemble jobs.
- **sweep_dir**: Path to the SWEEP directory where each subdirectory corresponds to an individual job’s configuration. Each directory in sweep_dir will be submitted as a separate job.
- **sweep_on_remote** (optional): Set to True if the SWEEP directory is located on the remote machine. Defaults to False, assuming the directory is local.
- **execute_put_configs** (optional): Set to True to transfer all configurations to the remote machine, or False to skip transferring if files are already available on the remote machine. Default is True.
- **upscale** (optional): A list of specific subdirectories within sweep_dir to include in the ensemble run. Use this if you want to rerun or upscale only a subset of configurations.
- **replica_start_number** (optional): The starting number for replica job numbering, allowing you to customise replica identification. Default is 1.
- **`**args`**: Additional arguments that can be passed to configure or modify job behaviour further as required by the specific environment or job scheduler.

#### Executing an Ensemble Job on a Remote Host

1. **Define the Remote Host**:
    - Ensure that the target machine is defined in machines.yml and that user login information is included in deploy/machines_user.yml.

2. **Run a Dummy Ensemble Job**:
    - To test the setup with a dummy job, use the command: `fabsim <machine_name> dummy_ensemble:dummy_test`.
    - This command performs the following steps:
      - a. **Copy Job Inputs**: Copies the input files from `plugins/FabDummy/config_files/dummy_test` to the remote location specified by remote_path_template in `deploy/machines.yml`. Machine-specific variables defined in `machines.yml` are substituted automatically.
      - b. **Transfer Inputs to Remote Results Directory**: Moves the input files to the designated results directory on the remote host.
      - c. **Substitute and Rename Input Files**: For each ensemble run, substitutes the input files found in `plugins/FabDummy/config_files/dummy_test/SWEEP`. The first input file is renamed in-place to `dummy.txt` for consistency in each ensemble run.
      - d. **Start the Remote Job**: Initiates the ensemble job on the remote host.
      - e. **Repeat Steps b–d**: Processes each base-level file or directory in `plugins/FabDummy/config_files/dummy_test/SWEEP`, submitting each as an individual job within the ensemble.

3. **Monitor Job Status**:
    - Use `fabsim <machine> stat` to check the submission status of your jobs, or `fabsim <machine> monitor` to periodically poll for job status updates.
    - If the stat or monitor commands no longer display any active jobs, all jobs have completed (successfully or otherwise).

4. **Retrieve Results**:
    - After completion, fetch the results from the remote machine using fabsim localhost fetch_results.
    - Investigate the output files stored in the local results/ subdirectories as needed.

#### Executing an Ensemble Job on a Remote Host with Replicas

Replicas allow you to run multiple identical jobs, which can yield varying outputs if the simulation algorithm includes stochastic or non-deterministic elements.

To run an ensemble job with N replicas, simply add `replicas=<N>` to your command. For example, to run a dummy ensemble with 5 replicas, use:

```bash
fabsim <machine_name> dummy_ensemble:dummy_test,replicas=5
```

This command will create N identical instances of each job in the ensemble, enabling you to gather data across multiple runs with the same configurations.

#### Using a VECMA Verification and Validation Pattern (VVP) to compare two code versions

FabDummy contains a minimal demonstrator script of VECMA VVP 2, which compares a candidate code version output with that of a stable intermediate form. You can run this little demonstrator by typing:

`fabsim localhost dummy_sif:dummy_test`

### Advanced Testing

#### Executing an ensemble job with QCG-PilotJob on a remote host

1. Ensure you are able to perform the first and second intermediate test.
2. Ensure that you have QCG-PilotJob installed on the remote machine.
3. Add QCG-PilotJob arguments by typing:

```sh
fabsim <machine_name> dummy_ensemble:dummy_test,replicas=5,cores=1,PJ=true,PJ_TYPE=QCG
```

Here, `PJ` indicates the job is a pilot job, and `PJ_TYPE` indicates the use of QCG-PilotJob.
