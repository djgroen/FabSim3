This document briefly details how user/developer can set up a remote machine on FabSim3 for job submission.

### Overview

The aim of FabSim3 is to automate and simplify the creation, management, execution and modification of complex application workflows using functionalities, such as ensemble runs, remote executions and code couplings. This helps researchers to become more productive in general, and more effective with handling complex applications in particular. For instance, researchers may want to run and rerun static configurations, run a range of slightly different workflows, or to define new types of complex applications altogether.

FabSim3 is built on top of the [Python Fabric library](http://www.fabfile.org/), and therefore shares automation and remote access features with Fabric (<http://www.fabfile.org>) and other system-level automation tools, such as Ansible (<http://www.ansible.com>) and Homebrew (<http://brew.sh>).

### FabSim3 Remote Job Management Command



#### Job submission

To submit a job on the remote machine, type
```sh
fab <remote machine name> <fabsim task>:<input parameters>
```
This does the following:

* create required files and folder on your local machine
* transfer all these files and folder to remote machine
* submit a job to the remote machine

#### Job Monitoring

* `stat`: returns a report for all submitted job(s).
```sh
fab <remote machine name> job_stat
```
By default it reports the status of jobs. You can also request a report status of specific job by
```sh
fab <remote machine name> job_stat:<jobID>
```

#### Fetching results

You can fetch the remote data using
```sh
fab <remote machine name> fetch_results
```

#### Cleaning up all remote directories

You can clear out ALL remote FabSim3 execution directories using
```sh
fab <remote machine name> clean_fabsim_dirs
```
NOTE: results will be lost if you did not fetch them first.

## How to add a new remote machine for use by the community
By default, a FabSim3 install will contain 3 machine-specific YML files:

* `FabSim3/fabsim/deploy/machines.yml`, which shows default values for machine-specific variables for each machine.
* `FabSim3/fabsim/deploy/machines_user.yml`, which shows user-specific values for machine-specific variables for each machine. This may include the name of the user account. This file is not committed to the repository.
* `FabSim3/fabsim/deploy/machines_user_example.yml`, a basic example of `machines_user.yml`

### Remote Machine Definition
To add a new machine definition, to be used by the community, one can add a corresponding entry to the `machines.yml` file. For example, for the Prometheus supercomputer in Cracow, Poland, this could be done as follow:
```yaml
prometheus:
  max_job_name_chars: 15
  job_dispatch: "sbatch"
  stat: "squeue"
  run_command: "mpiexec -n $cores"
  batch_header: slurm-prometheus
  remote: "prometheus.cyfronet.pl"
  home_path_template: "/net/people/$username"
  runtime_path_template: "/net/scratch/people/$username"
  modules: ["load apps/lammps"]
  temp_path_template: "$work_path/tmp"
  queue: "plgrid"
  python_build: "python2.7"
  corespernode: 24
```
When defining a new machine in this way, all variables will by default have a value that is specified under the `#!yaml "default:"` heading of `machines.yml`.  

We recommend commiting these type of definitions to the GitHub repository of FabSim3, unless the machine is non-public.  
In that case, create `machines_private.yml` in the same directly and add all non-public machines to it.

#### Adding user information for an existing machine

User information for an existing machine can be added in `machines_user.yml`. Any variable set here will supersede the value in `machines.yml`. For example, for the ARCHER supercomputer, one can enter user information as follows:
```yaml
archer:
  username: "ucljames"
  project: "e283"
  budget: "e283-suter"
  lammps_exec: "/home/e283/e283/ucljames/lmp_xc30" # custom variable overwrite
```
#### Changing connectivity settings for specific machines  
Please note that some connectivity settings are not explicitly exposed as FabSim3 environment variables, but are present in the `env` through the original fabric environment variables. An example of such a variable is port, which indicates the port that any SSH connection would rely on.

A full list of fabric `env` variables can be found on <www.fabfile.org>, e.g. here: <http://docs.fabfile.org/en/1.14/usage/env.html>.

#### Adding shortened commands for specific machines

In FabSim3, it is possible to introduce a shortened alias. For instance, you can define a `fab` command to use in place of `fab eagle_vecma`. Such aliases can help speed up the typing of interactive commands.

To define an alias, simply type
```sh
fabsim <remote machine name> bash_machine_alias:name=<name_of_alias>
```
So, given the previous example, one could type
```sh
fabsim eagle_vecma bash_machine_alias:name=feh
```
Aliases are stored in `FabSim3/fabsim/bin` and cannot be named `fabsim`, as that would break the main `fabsim` command.

!!! note
	This has to be done for every user, as different people have different existing shell commands, and we want to avoid accidental conflicts.

### QCG Pilot Job Manager

A Pilot Job is a container for many subjobs that can be started and managed without having to wait individually for resources to become available.

The [QCG PilotJob](https://github.com/vecma-project/QCG-PilotJob) mechanism provides two interfaces that may be used interchangeably. The first one allows to specify a file with the description of sub-jobs and execute the scenario in a batch-like mode, conveniently supporting static scenarios. The second interface is offered with the REST API and it can be accessed remotely in a more dynamic way. It will be used to support scenarios where a number of replicas and their complexity dynamically changes at application runtime.

Within FabSim3, you can install this python library or any other python library required for your application as a python virtual environment in your account.

#### QCG-PJ installation on your remote machine

To install QCG-PJ on your remote machine, simply type:
```sh
fabsim <remote machine name> install_app:QCG-PilotJob,venv=True
```
Here, the `venv=True` ensures that you are using the VirtualEnv virtual environment. If you choose to omit the flag, you may have to face various errors and complications that accompany direct deployment in the default remote machine environment.
!!! info
	All required packages are downloaded and transferred to the remote machine. Therefore, even if the compute nodes do not have an access to Internet, the installation part will be done in off-line mode

#### Python packages installation on your remote machine

If you application requires a python package, which is not available on pre-installed packages on your remote machine, you can install it as your local virtual environment. To do that, please specify the package name in `FabSim3/fabsim/deploy/applications.yml`under `packages` entry
```yaml
packages:
    - matplotlib
```
and then type
```sh
fabsim <remote machine name> install_packages:venv=True
```
