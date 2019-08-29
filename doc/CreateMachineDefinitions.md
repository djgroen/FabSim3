# Create Machine Definitions

## Startup

See main documentation.

## YML file structure

By default, a FabSim3 install will contain 3 machine-specific YML files:
- machines.yml, which shows default values for machine-specific variables for each machine.
- machines_user.yml, which shows user-specific values for machine-specific variables for each machine. This may include the name of the user account. This file is *not* committed to the repository.
- machines_user_example.yml, a basic example of machines_user.yml

## Adding a new machine to be used by the community

To add a new machine definition, to be used by the community, one can add a corresponding entry to the machines.yml file. For example, for the Prometheus supercomputer in Cracow, Poland, this could be done as follow:

```
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

When defining a new machine in this way, all variables will by default have a value that is specified under the "default:" heading of machines.yml.

We recommend commiting these typo of definitions to the GitHub repository of FabSim3, unless the machine is non-public.

## Adding user information for an existing machine

User information for an existing machine can be added in machines_user.yml. Any variable set here will supersede the value in machines.yml. For example, for the ARCHER supercomputer, one can enter user information as follows:

```
archer:
  username: "ucljames"
  project: "e283"
  budget: "e283-suter"
  lammps_exec: "/home/e283/e283/ucljames/lmp_xc30" # custom variable overwrite
```

## Changing connectivity settings for specific machines

Please note that some connectivity settings are not explicitly exposed as FabSim3 environment variables, but are present in the env through the original fabric environment variables. An example of such a variable is `port`, which indicates the port that any SSH connection would rely on.

A full list of fabric env variables can be found on www.fabfile.org, e.g. here: http://docs.fabfile.org/en/1.14/usage/env.html

## Adding shortened commands for specific machines.

Note: this has to be done for every user, as different people have different existing shell commands, and we want to avoid accidental conflicts.

In FabSim3 it is possible to introduce a shortened alias. For instance, you can define a `feh` command to use in place of `fab eagle_hidalgo`. Such aliases can help speed up the typing of interactive commands.

To define an alias, simply type `fabsim <machine_name> bash_machine_alias:name=<name_of_alias>`. So, given the previous example, one could type `fabsim eagle_hidalgo bash_machine_alias:name=feh`.

Aliases are stored in `$FabSim3/bin` and cannot be named `fabsim`, as that would break the main fabsim command.
