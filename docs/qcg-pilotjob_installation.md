# QCG Pilot Job installation on remote machines

QCG Pilot Job is a lightweight implementation of the Pilot Job mechanism which
can be used to run a very large number of jobs efficiently on remote clusters and supercomputers.

More information on QCG-PilotJob can be found on their [ReadTheDocs site](https://qcg-pilotjob.readthedocs.io/en/develop/).

<p align="center">
    <img src="../images/qcg-pj.png" alt="Image of a QCG Pilot Job container" width="800" />
</p>
*Example of a QCG-Pilotjob container, which dynamically facilitates a diverse set of code executions within a single queuing system job. [Source](https://link.springer.com/chapter/10.1007/978-3-030-77977-1_39)*

Here we present how you can install QCG Pilot Job on remote machines so that you can use it with FabSim3.

!!! note
    Note that FabSim3 can also work with a pre-installed version of QCG-PilotJob; but for those who need to set it up manually this document is meant to provide some help.

## Prerequisites

The basic prerequisites for installing QCG-PilotJob on a remote machine using FabSim3 are:

- FabSim3 properly installed and configured on your local machine
- SSH access to the remote machine
- Python 3.6 or newer on the remote machine

In most cases, QCG-PilotJob can be installed directly with pip without additional dependencies. However, for certain computational workloads, particularly those involving numerical computations, the following optional packages may improve performance:

```sh
# Optional: Install these if you encounter performance issues with numerical computations
sudo apt install libopenblas-dev pkg-config libopenblas64-dev
```

These libraries provide optimized implementations of linear algebra operations which may benefit certain types of simulations, but they are not strictly required for basic QCG-PilotJob functionality.

!!! note On HPC systems like ARCHER2, the required mathematical libraries are typically already available as modules, so no additional installation is necessary.

## Installation Methods

There are two methods available for installing QCG-PilotJob: direct installation and job-based installation.

### Method 1: Direct Installation (Recommended)

This method directly installs QCG-PilotJob through a SSH connection, without requiring a job submission. This is faster and simpler for most use cases.

#### Step 1: Create a Virtual Environment (Recommended)

First, create a virtual environment on the remote machine (e.g., archer2):

```sh
fabsim <remote_machine> create_virtual_env
```

This command will:

- Create a Python virtual environment on the remote machine
- Display the path where the environment was created
- Provide instructions for updating your configuration

#### Step 2: Update Your machines_user.yml

Add the virtual_env_path parameter to your machine configuration in machines_user.yml as instructed by the previous command output:

```sh
<remote_machine>:
  virtual_env_path: "/path/shown/in/previous/command/output"
```

#### Step 3: Install QCG-PilotJob

Install QCG-PilotJob into the virtual environment:

```sh
fabsim <remote_machine> direct_install_app:QCG-PilotJob,venv=True
```

This command will:

- Activate the virtual environment on the remote machine
- Install QCG-PilotJob directly using pip
- Verify the installation

### Method 2: Job-Based Installation (Legacy)

This method installs QCG-PilotJob by submitting an installation job to the remote machine's queuing system.

```sh
fabsim <remote_machine> install_app:QCG-PilotJob,venv=True
```

- Miniconda will be installed locally.
- All the dependencies required for installation of QCG Pilot Job will be installed locally
- Prepares the script that when run on the remote machine will install QCG Pilot Job
- Transfers all the dependencies to the remote machine
- Submits the installation job script to the remote machine

Since the number of dependencies for QCG Pilot Job is quite large, therefore, the command may take up to 45 minutes to run.

After all the above-mentioned processes are done, the status of the submitted job on the remote machine can be checked using:

```sh
fabsim <remote_machine> stat
```

Once the submitted job completes successfully, QCG Pilot Job will be installed on the remote machine.

### Machine-Specific Notes

For ARCHER2, the direct installation method will automatically:

- Load the cray-python module before installation
- Create and use a virtual environment if specified
- Configure appropriate paths

Your ARCHER2 configuration in machines_user.yml should include:

```sh
archer2:
  username: <your-username>
  # Other ARCHER2 settings
  virtual_env_path: "/work/<budget>/<project>/<username>/FabSim3/VirtualEnv"
```

## Expanded Verification and Usage Examples

After installing QCG-PilotJob, you'll want to verify the installation and understand how to use it with FabSim3. This section provides a comprehensive guide to testing and using QCG-PilotJob in various scenarios.

### Installing the Test Plugin

First, you need to install the FabDummy plugin, which provides simple test cases to verify QCG-PilotJob functionality:

```sh
fabsim localhost install_plugin:FabDummy
```

This command installs a lightweight plugin containing sample tasks specifically designed to test and demonstrate FabSim3's capabilities with workflow managers like QCG-PilotJob.

#### Basic Ensemble Execution

The simplest way to verify QCG-PilotJob integration is by running a basic ensemble test:

```sh
fabsim localhost dummy_ensemble:dummy_test,PJ_TYPE=qcg,venv=true
```

This command:

- Runs the `dummy_test` from the FabDummy plugin
- Uses QCG-PilotJob as the workflow manager (`PJ_TYPE=qcg`)
- Activates the Python virtual environment where QCG-PilotJob is installed (`venv=true`)
- Processes all sample directories in the SWEEP directory as separate tasks

The `venv=true` parameter is crucial as it instructs FabSim3 to use the QCG-PilotJob installation from your Python virtual environment rather than any system-wide installation.

You should see output confirming task submission, execution, and completion. If this works successfully, your QCG-PilotJob installation is functioning correctly.

#### Advanced Usage Patterns

QCG-PilotJob with FabSim3 supports several advanced execution patterns. Here are key examples:

Running Jobs with Replicas
Replicas allow you to run the same task multiple times, which is useful for gathering statistics or running Monte Carlo simulations:

```sh
fabsim localhost dummy_ensemble:dummy_test,replicas=2,PJ_TYPE=qcg,venv=true
```

This command:

- Takes each directory in the SWEEP directory and creates a task from it
- Runs each task twice (2 replicas)
- Results in a total number of executions equal to (number of directories × 2)

Replicas are useful when you need to run the same simulation multiple times with identical parameters, for example in stochastic simulations where you want to capture the range of possible outcomes.

#### Upsampling for Task Distribution

Upsampling allows different directories to have different numbers of replicas:

```sh
fabsim localhost dummy_ensemble:dummy_test,upsample="d1;d2",replicas="3;2",PJ_TYPE=qcg,venv=true
```

This command creates:

- 3 identical tasks from directory d1
- 2 identical tasks from directory d2
- A total of 5 tasks executed by QCG-PilotJob

Upsampling is particularly useful when different parameter sets require different numbers of replicas, such as when some parameter regions need more samples to achieve statistical significance.

#### Task Prioritization with QCG-PilotJob

QCG-PilotJob allows you to prioritize specific tasks using the `exec_first` parameter:

```sh
fabsim localhost dummy_ensemble:dummy_test,upsample="d1;d2",replicas="3;2",exec_first="d2",PJ_TYPE=qcg,venv=true
```

This command:

- Creates tasks as in the upsampling example above
- Ensures tasks from directory `d2` are executed before tasks from `d1`
- Helps manage dependencies or prioritize more important computations

Task prioritization is valuable when some simulations produce results needed by other simulations, or when you want to get results from certain parameter sets earlier in the execution.

#### Resources Handling

QCG-PilotJob offers resource management capabilities when executing on HPC systems. You can control how resources are allocated to individual tasks within your ensemble:

#### Specifying Nodes and Cores

You can specify the number of nodes and cores per task:

```sh
fabsim <remote_machine> dummy_ensemble:dummy_test,PJ_nodes=1,PJ_cores=4,PJ_TYPE=qcg,venv=true
```

This assigns 4 cores on 1 node to each task in your ensemble. You can adjust these values based on your application's parallelization needs.

##### Wall Time Limits

To manage execution time, you can set specific time limits for the overall job:

```sh
fabsim <remote_machine> dummy_ensemble:dummy_test,job_wall_time=1:00:00,PJ_TYPE=qcg,venv=true
```

This sets a one-hour time limit for the entire ensemble job.

##### Examining Results

After your job completes, you can fetch and analyze the results:

```sh
fabsim <remote_machine> fetch_results
```

Results are stored in the `results` directory, organized by job name and timestamp. Look for the QCG file, which contains detailed information about how QCG-PilotJob managed your tasks, including resource allocation, task scheduling, and execution times.

I'd be happy to expand the verification section with more descriptive text and explanations:

### Verification and Usage Examples

After installing QCG-PilotJob, you'll want to verify the installation and understand how to use it with FabSim3. This section provides a comprehensive guide to testing and using QCG-PilotJob in various scenarios.

#### Installing the FabDummy Test Plugin

First, you need to install the FabDummy plugin, which provides simple test cases to verify QCG-PilotJob functionality:

```sh
fabsim localhost install_plugin:FabDummy
```

This command installs a lightweight plugin containing sample tasks specifically designed to test and demonstrate FabSim3's capabilities with workflow managers like QCG-PilotJob.

### Running a Basic Ensemble Test

The simplest way to verify QCG-PilotJob integration is by running a basic ensemble test:

```sh
fabsim localhost dummy_ensemble:dummy_test,PJ_TYPE=qcg,venv=true
```

This command:

- Runs the `dummy_test` from the FabDummy plugin
- Uses QCG-PilotJob as the workflow manager (`PJ_TYPE=qcg`)
- Activates the Python virtual environment where QCG-PilotJob is installed (`venv=true`)
- Processes all sample directories in the SWEEP directory as separate tasks

The `venv=true` parameter is crucial as it instructs FabSim3 to use the QCG-PilotJob installation from your Python virtual environment rather than any system-wide installation.

You should see output confirming task submission, execution, and completion. If this works successfully, your QCG-PilotJob installation is functioning correctly.

### Additional Advanced Usage Patterns

QCG-PilotJob with FabSim3 supports several advanced execution patterns. Here are key examples:

#### Running Jobs with Replicas

Replicas allow you to run the same task multiple times, which is useful for gathering statistics or running Monte Carlo simulations:

```sh
fabsim localhost dummy_ensemble:dummy_test,replicas=2,PJ_TYPE=qcg,venv=true
```

This command:

- Takes each directory in the SWEEP directory and creates a task from it
- Runs each task twice (2 replicas)
- Results in a total number of executions equal to (number of directories × 2)

Replicas are useful when you need to run the same simulation multiple times with identical parameters, for example in stochastic simulations where you want to capture the range of possible outcomes.

#### Using Upsampling for Task Distribution

Upsampling allows different directories to have different numbers of replicas:

```sh
fabsim localhost dummy_ensemble:dummy_test,upsample="d1;d2",replicas="3;2",PJ_TYPE=qcg,venv=true
```

This command creates:

- 3 identical tasks from directory `d1`
- 2 identical tasks from directory `d2`
- A total of 5 tasks executed by QCG-PilotJob

Upsampling is particularly useful when different parameter sets require different numbers of replicas, such as when some parameter regions need more samples to achieve statistical significance.

#### Setting Task Priorities

QCG-PilotJob allows you to prioritize specific tasks using the `exec_first` parameter:

```sh
fabsim localhost dummy_ensemble:dummy_test,upsample="d1;d2",replicas="3;2",exec_first="d2",PJ_TYPE=qcg,venv=true
```

This command:

- Creates tasks as in the upsampling example above
- Ensures tasks from directory `d2` are executed before tasks from `d1`
- Helps manage dependencies or prioritize more important computations

Task prioritization is valuable when some simulations produce results needed by other simulations, or when you want to get results from certain parameter sets earlier in the execution.

### Advanced Resources Handling

QCG-PilotJob offers sophisticated resource management capabilities when executing on HPC systems. You can control how resources are allocated to individual tasks within your ensemble:

#### Controlling Nodes and Cores

You can specify the number of nodes and cores per task:

```sh
fabsim <remote_machine> dummy_ensemble:dummy_test,PJ_nodes=1,PJ_cores=4,PJ_TYPE=qcg,venv=true
```

This assigns 4 cores on 1 node to each task in your ensemble. You can adjust these values based on your application's parallelization needs.

#### Memory Allocation

For memory-intensive applications, you can specify memory requirements:

```sh
fabsim <remote_machine> dummy_ensemble:dummy_test,PJ_memory=4GB,PJ_TYPE=qcg,venv=true
```

This ensures each task receives at least 4GB of memory.

#### Setting Wall Time Limits

To manage execution time, you can set specific time limits for the overall job:

```sh
fabsim <remote_machine> dummy_ensemble:dummy_test,job_wall_time=1:00:00,PJ_TYPE=qcg,venv=true
```

This sets a one-hour time limit for the entire ensemble job.

### Fetching and Examining Results

After your job completes, you can fetch and analyze the results:

```sh
fabsim <remote_machine> fetch_results
```

Results are stored in the `results` directory, organized by job name and timestamp. Look for the `QCG_PILOT_OUT` file, which contains detailed information about how QCG-PilotJob managed your tasks, including resource allocation, task scheduling, and execution times.

### Troubleshooting

If you encounter issues with QCG-PilotJob execution:

1. Check that the virtual environment path is correctly set in your `machines_user.yml`
2. Verify that QCG-PilotJob is correctly installed with `fabsim <remote_machine> direct_install_app:QCG-PilotJob,venv=True`
3. Examine job logs in the results directory for specific error messages
4. For `ARCHER2` or other specific HPC systems, ensure the appropriate modules are loaded before job execution

