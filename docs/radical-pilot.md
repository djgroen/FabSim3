# FabSim3 and RADICAL-Pilot Integration Documentation

## Introduction
This documentation provides detailed instructions on how to configure, use, and troubleshoot the RADICAL-Pilot (RP) integration in FabSim3.

### Prerequisites
- Python 3.6 or higher
- RADICAL-Pilot
- FabSim3

### Installing FabSim3 and RADICAL-Pilot
1. **Set up and Activate your Python virtual environment (optional but recommended):**
    ```bash
    mkdir -p ~/workspace
    cd ~/workspace
    python3 -m venv VirualEnv
    source VirtualEnv/bin/activate
    ```

2. **Clone FabSim3 repository:**
    ```bash
    git clone https://github.com/djgroen/FabSim3.git
    cd FabSim3
    ```

3. **Install FabSim3 dependencies:**
    ```bash
    python3 configure_fabsim.py
    ```

4. **Install RADICAL-Pilot:**
    ```bash
    fabsim <machine> install_app:RADICAL-Pilot,venv=True
    ```

## Configuration

### Example Parameters Configuration for RADICAL
Although these parameters belong to RADICAL, not all of them need to be configured. The required ones are noted in the following section.

```yaml
resource: ''           # The target computing resource (e.g., 'local.localhost', 'epcc.archer2') where the job will be submitted.
project: ''            # The project or allocation under which the job will be run. This is often required by HPC centers to track resource usage.
queue: ''              # The queue or partition name on the resource where the job should be submitted. This can affect scheduling priority and available resources.
runtime: 60            # The maximum runtime for the job in minutes. The job will be terminated if it exceeds this time limit.
nodes: 1               # The number of nodes required for the job. This depends on the scale and parallelism of the application.
executable: ''         # The path to the executable or script that will be run for the job. This should be accessible on the target resource.
arguments: '[]'        # A list of command-line arguments to pass to the executable. This can be used to customize the job behavior.
pre_exec: '[]'         # A list of shell commands to run before executing the main job script. This can be used for setting up the environment.
ranks: 1               # The number of MPI ranks or processes to launch for the job. This is relevant for parallel applications.
cores_per_rank: 1      # The number of CPU cores to allocate per MPI rank or process. This can be used to control threading within ranks.
sandbox: ''            # The working directory where job-related files will be stored and accessed. This should be a path on the target resource.
```

### Adding RADICAL Parameters to machines_user.yml
In your `machines_user.yml`, add the RADICAL-Pilot specific parameters under the appropriate machine section. For example, for `archer2`:

```yaml
archer2:
  username: your_username
  manual_ssh: true
  flee_location: /work/$project/$project/your_username/flee
  virtual_env_path: /work/$project/$project/your_username/VirtualEnv
  remote: archer2
  project: $project
  budget: $budget
  job_wall_time: '10:00:00'
  run_prefix_commands:
    - export PYTHONUSERBASE=/work/$project/$project/your_username/.local
    - 'export PATH=$PYTHONUSERBASE/bin:$PATH'
    - 'export PYTHONPATH=$PYTHONUSERBASE/lib/python3.8/site-packages:$PYTHONPATH'
  partition_name: "standard" # RADICAL-Pilot partition name
  qos_name: "short"          # RADICAL-Pilot qos name
  runtime: 10                # RADICAL-Pilot runtime in minutes
  nodes: 1                   # RADICAL-Pilot nodes 
  ranks: 1                   # RADICAL-Pilot ranks 
  cores_per_rank : 1         # RADICAL-Pilot cores per rank
```

## Usage

### Running Jobs with RADICAL-Pilot
To submit jobs using RADICAL-Pilot, use the PJ and PJ_TYPE arguments in your command. Here’s an example command to run an ensemble job with RADICAL-Pilot (RP):
    ```bash
    fabsim <machine> <function>:config=<config_files>,<additional_arguments>,PJ=true,PJ_TYPE=RP,venv=true
    ```

### Running Specific Jobs with RADICAL-Pilot
For running specific jobs like FabDummy in replica mode:

```bash
fabsim archer2 dummy:config=dummy_test,replicas=2,cores=4,PJ=true,PJ_TYPE=RP,venv=true
```

For running specific jobs in ensemble mode:

```bash
fabsim archer2 dummy_ensemble:config=dummy_test,replicas=2,cores=4,PJ=true,PJ_TYPE=RP,venv=true
```

## Troubleshooting

### Common Issues and Solutions
1. Job Submission Fails Due to Time Limit:

    - Ensure that the job_wall_time is correctly set in the machines_user.yml file.
    - Check if the qos setting allows for the specified wall time.

2. Missing or Incorrect 'PJ', 'PJ_TYPE' Argument:

    - Ensure that you have included PJ=true and PJ_TYPE=RP or PJ_TYPE=QCG-PJ in your command.

3. Python Package Installation Issues:

    - Ensure that RADICAL-Pilot is installed in your virtual environment and venv is set to true.
    - Verify that the virtual environment is activated before running the FabSim3 commands.
    - To check if RADICAL-Pilot is installed, you can use the following Python command:
        ```bash
        python3 -c 'import RADICAL.pilot' && echo "RADICAL-Pilot is installed." || echo "RADICAL-Pilot is NOT installed."
        ```

## Contributing
We welcome contributions to improve the RADICAL-Pilot integration in FabSim3. Please follow the standard GitHub pull request process.

## Contact
For any questions or support, please contact FabSim3 Support.

