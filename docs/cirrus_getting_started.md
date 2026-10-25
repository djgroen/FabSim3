# Getting started with Cirrus (EPCC)

A step-by-step guide for people who have never used a supercomputer before.

It covers how to log in to Cirrus, how the machine is organised, how to run
your first job, and how to avoid wasting compute time (Cirrus is charged per
core-hour). Everything before section 9 is plain Cirrus usage and works with
any terminal.

Section 9 is only needed if you want to use
[FabSim3](https://fabsim3.readthedocs.io) and Cirrus: it links to the
FabSim3 documentation and lists the three settings that differ on Cirrus.

---

## 0. Before you start

You need three things. If one is missing, contact the workshop organiser (or
EPCC support) **before** the session, not during it.

| What | Why you need it | Example |
|---|---|---|
| A Cirrus account | Cirrus only accepts registered users | username `tc078user5` |
| Your project (and budget) code | Jobs are charged to a project | `tc078` |
| An SSH key registered with Cirrus | This is how the machine recognises you | `~/.ssh/id_ed25519.pub` |

You will also need a **one-time password (TOTP)** from an authenticator app
on your phone (Google Authenticator, Microsoft Authenticator, ...). EPCC
registers this as part of the account setup; the registration details are in
the "multi-factor authentication" section of your account email.

!!! note
        On Cirrus the username usually has the project code in front of it, e.g.
        project `tc078` and user `5` gives the username `tc078user5`. Your
        project code is what jobs are charged against.

### The mental model (read this once)

```
      your laptop                 Cirrus
 ┌────────────────┐          ┌──────────────────────────────────┐
 │  terminal      │  ssh     │  login node (login.cirrus.ac.uk) │
 │  ssh client    │ ───────► │  - you type here                 │
 └────────────────┘          │  - shared by many users          │
                             │  - do NOT run big jobs here      │
                             └───────────┬──────────────────────┘
                                         │  you ask the scheduler for resources
                                         ▼
                             ┌──────────────────────────────┐
                             │  Slurm scheduler             │
                             │  - queues your job           │
                             │  - allocates nodes + cores   │
                             └───────────┬──────────────────┘
                                         │
                             ┌───────────▼──────────────────┐
                             │  compute node (cs-n0123)     │
                             │  - runs your job             │
                             │  - 288 cores each            │
                             └──────────────────────────────┘
```

Three things to remember:

1. **You log in to a *login* node.** It is shared with everybody. Typing is
   fine, long calculations are not (they would slow everyone down).
2. **Real work happens on *compute* nodes**, and only after the scheduler
   (Slurm) has given you one.
3. **Your files live on a *network filesystem*** (`/epccfs`), which is visible
   from the login node and from the compute nodes. A file you create on the
   login node can be read by your job.

!!! tip
        If the workshop uses **FabSim3** to submit the jobs, read
        [section 9](#9-using-fabsim3-from-cirrus) as well: FabSim3 hides
        most of what is described below, but it needs three extra
        settings for Cirrus, and the login details in sections 1-4 still
        apply.

---

## 1. Set up your SSH key

SSH keys are how you prove your identity. Cirrus never accepts a plain
password; it needs a key, plus (because of multi-factor authentication) a
one-time code.

Check whether you already have a key:

```sh
ls ~/.ssh/id_ed25519.pub ~/.ssh/id_rsa.pub
```

If nothing is listed, create one:

```sh
ssh-keygen -t ed25519 -C "your.email@example.com"
```

Press Enter to accept the default file location. You will be asked for a
**passphrase** — use one you can remember; you will be asked for it every
time you log in (unless you set up an SSH agent, see the note below).

!!! note
        To avoid typing the passphrase repeatedly, add this to `~/.ssh/config`:

        ```sh
        Host *
           AddKeysToAgent yes
           UseKeychain yes
        ```

        (`UseKeychain` is macOS only; on Linux, `ssh-add` after `ssh-keygen`
        achieves the same.)

Now show the **public** key (the file ending in `.pub`, never the private one):

```sh
cat ~/.ssh/id_ed25519.pub
```

Copy that whole line and register it with Cirrus. EPCC's account management
page lets you add an SSH public key to your account; if you cannot find the
option, send the public key to EPCC support and ask them to add it.

!!! warning
        The private key (`~/.ssh/id_ed25519`, without `.pub`) stays on your
        laptop and must never be sent to anybody, including the organisers.

---

## 2. Tell your computer how to reach Cirrus

Typing the full command every time gets tiring. Create an *alias* for Cirrus
in `~/.ssh/config` (Linux/macOS; on Windows see the note below).

Create the file if it does not exist, then add this block, replacing
`<your-username>` with your Cirrus username:

```sh
Host cirrus
   User <your-username>
   HostName login.cirrus.ac.uk
   ServerAliveInterval 60
   ControlPath ~/.ssh/control-%r@%h:%p
   ControlMaster auto
   ControlPersist 12h
```

What the last three lines do: they keep **one** connection open in the
background for 12 hours, and reuse it for every later command. This matters
because of multi-factor authentication — without this, *every* `ssh`, `scp`
and `rsync` would ask for a fresh one-time code.

!!! note
        If your key has a name other than the default (`id_ed25519`, `id_rsa`),
        add these two lines to the block:

        ```sh
           IdentityFile ~/.ssh/<your-key-name>
           IdentitiesOnly yes
        ```

!!! note
        **Windows users:** the same block works in
        `C:\Users\<you>\.ssh\config`. The multiplexing lines are not needed on
        Windows because Windows OpenSSH does not support `ControlMaster`; you
        will simply be asked for the one-time code each time. For FabSim3 on
        Windows, see the [Windows installation guide](installation.md).

---

## 3. Log in

```sh
ssh cirrus
```

What happens:

1. Your key is offered. If the key has a passphrase, you are asked for it.
2. You are asked for a **one-time code** (6 digits) from your authenticator
   app. This is the multi-factor authentication step.

If everything is correct you land on a prompt that looks like this:

```text
username@login03:~$
```

Check that you are who you think you are:

```sh
whoami      # your Cirrus username
hostname    # e.g. login03
pwd         # your home directory
```

To leave Cirrus, type `exit`.

!!! warning
        **Never run your actual simulation on the login node.** It is shared
        with every other user. Use a batch job (step 6) instead.

---

## 4. Log in only once (multiplexing)

Because of the one-time code, logging in repeatedly is painful. The
`ControlMaster` block from step 2 solves this: log in once, and the
background connection is reused for the next 12 hours.

Check that the background connection is alive:

```sh
ssh -O check cirrus
```

Expected output:

```text
Master running (pid=12345)
```

If it says *"Master connection does not exist"*, just run `ssh cirrus` once
more to create it.

Close the background connection when you are done for the day:

```sh
ssh -O exit cirrus
```

!!! note
        With multiplexing in place you can also run `ssh cirrus` again later
        without typing a code: the new session simply rides on the existing
        connection.

---

## 5. Find out what the machine looks like

Useful first commands (all of them run on the login node):

```sh
sinfo              # which partitions exist and how busy they are
squeue             # jobs currently running or waiting (yours and others')
sacct -u $USER -S today --format=JobID,JobName%20,State,Elapsed,AllocCPUS,AllocNodes
```

Example `sinfo` output on Cirrus:

```text
PARTITION AVAIL  TIMELIMIT   NODES(A/I/O/T) NODELIST
standard     up   infinite    565/42/33/640 cs-n[0000-0519,0528-0535,...]
highmem      up   infinite        57/3/4/64 cs-n[0192-0255]
```

* `standard` — 640 nodes, 288 cores and 768 GB of memory each.
* `highmem` — 64 nodes with 1536 GB of memory each, for jobs that need a lot
  of RAM.

### Where to put your files

```sh
ls /epccfs/            # the shared work area of the machine
cd /epccfs/<project>/<project>/<username>
```

| Path | Use it for | Notes |
|---|---|---|
| `/epccfs/<project>/<project>/<username>` | **Your working directory** | visible to the login node *and* to compute nodes; this is where job input and output files go |
| `/home/<username>` | small files, dotfiles | mounted on the **login nodes only** — a job cannot read it |
| `/work/...` | nothing | deprecated and read-only |

!!! warning
        If your job writes to `/home`, it will fail. Write to `/epccfs`.

Check how much space you are using:

```sh
du -sh /epccfs/<project>/<project>/<username>
```

### Software

Cirrus uses *modules*. A module is a named, versioned piece of software; you
load the one you want:

```sh
module avail python        # what is on offer
module load python/3.11.7  # load one
python3 --version          # check it worked
```

!!! note
        The `module` command only works in a **login shell**. In scripts and
        non-interactive commands you may need `bash -lc "module load ..."`.
        In batch scripts, use `#!/bin/bash --login` as the first line and the
        modules are available automatically.

---

## 6. Run your first job

A *batch job* is a script that the scheduler runs for you on a compute node.
You do not need to be logged in while it runs.

### Step 6.1 — write the script

```sh
cd /epccfs/<project>/<project>/<username>
mkdir -p workshop
cd workshop
```

Create a file called `hello.sh`:

```sh
cat > hello.sh <<'EOF'
#!/bin/bash --login
#SBATCH --job-name=hello
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:05:00
#SBATCH --account=<your-project>
#SBATCH --partition=standard
#SBATCH --qos=standard
#SBATCH --output=hello-%j.out
#SBATCH --error=hello-%j.err

echo "Hello from job $SLURM_JOB_ID"
echo "Running on node $(hostname)"
echo "Started at $(date)"
sleep 30
echo "Finished at $(date)"
EOF
```

Lines starting with `#SBATCH` are *directives*: they are read by the scheduler
before the job starts.

| Directive | Meaning |
|---|---|
| `--job-name` | name shown in the queue |
| `--nodes` | number of compute nodes |
| `--ntasks` | number of tasks (usually 1 for serial work) |
| `--cpus-per-task` | cores per task |
| `--time` | maximum wall-clock time, `HH:MM:SS` |
| `--account` | the project/budget the job is charged to |
| `--partition` | `standard` or `highmem` |
| `--qos` | quality of service; `standard` is the normal one |
| `--output` / `--error` | where stdout / stderr are written (`%j` = job id) |

### Step 6.2 — submit it

```sh
sbatch hello.sh
```

You get back something like:

```text
Submitted batch job 579901
```

That is the **job id**. Write it down — you use it everywhere else.

### Step 6.3 — watch it

```sh
squeue -u $USER          # is my job running, waiting, or done?
```

```text
JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST
579901    standard   hello  youruser  R      0:10      1 cs-n0123
```

`ST` is the state: `PD` pending (waiting), `R` running, `CD` completed,
`CA` cancelled.

### Step 6.4 — read the result

When the job is finished, its output is in the file you named:

```sh
cat hello-579901.out
```

```text
Hello from job 579901
Running on node cs-n0123
Started at Tue Oct 21 10:03:11 BST 2026
Finished at Tue Oct 21 10:03:41 BST 2026
```

Check the accounting (how long it ran, how many cores it used):

```sh
sacct -j 579901 --format=JobID,JobName%20,State,Elapsed,AllocCPUS,AllocNodes,ExitCode
```

```text
JobID                   JobName  State    Elapsed  AllocCPUS AllocNodes ExitCode
579901                  hello  COMPLETED   00:00:31          1          1     0:0
```

`AllocCPUS` is the number of cores you were **charged** for. `ExitCode 0:0`
means success.

### Step 6.5 — stop a job

```sh
scancel 579901
```

!!! tip
        Copy the output file *before* resubmitting with the same name: Slurm
        will not overwrite an existing output file, and the new job will fail
        with an error if the file exists.

---

## 7. The three Cirrus rules that catch people out

### 7.1 You are charged per core-hour

Cirrus bills the number of cores you were given, multiplied by the time your
job ran. A job that asks for one core and runs for one hour costs 1 core-hour.
A job that asks for 288 cores (a whole node) and runs for one hour costs
288 core-hours — 288 times more.

So **request only what you need**:

```sh
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8      # 8 cores, not 288
```

A node is shared between jobs by default: if you ask for 8 cores on a node
that has 288, you are charged for 8 and the other 280 stay available to
other users.

!!! warning
        If you need the *whole* node (for example for a memory-heavy
        application), add `--exclusive`. You will then be charged for all
        288 cores, whether you use them or not.

### 7.2 More than one node requires `--exclusive`

If your job asks for more than one node, Cirrus refuses to start it:

```text
sbatch: error: Job rejected: Nodes specified but the --exclusive flag is not
specifed. Please use the --exclusive flag if you need to specify nodes, or
specify tasks or cpus(cores) if not.
```

The fix is to add `--exclusive` to your script:

```sh
#SBATCH --nodes=2
#SBATCH --exclusive
```

A two-node job like that is charged for 2 × 288 = 576 cores for as long as it
runs, so keep multi-node jobs short.

### 7.3 Jobs can wait a long time before they start

If you submit while the machine is busy, your job stays `PD` (pending). The
reason is shown in the last column of `squeue`:

```text
579901    standard   hello  youruser PD      0:00      1 (ReqNodeNotAvail, UnavailableNodes:cs-n[...])
```

`ReqNodeNotAvail` usually means nodes are being drained for maintenance or
the machine is simply busy. It is not a problem with your script — the job
starts automatically once a node is free. Cirrus also periodically drains
large parts of the machine, so a job that ran yesterday may wait much longer
today.

Use the time to check your script with a very short run, and ask for a short
`--time` limit so that a job that hangs does not burn your allocation:

```sh
#SBATCH --time=00:10:00
```

---

## 8. A little more practice

### Interactive jobs (useful for debugging)

To experiment on a compute node, ask for one and get a shell on it:

```sh
salloc --nodes=1 --cpus-per-task=4 --time=00:30:00 --partition=standard --qos=standard --account=<your-project>
```

You are now on a compute node; run your commands, then type `exit` to give
the node back. Interactive jobs are billed in exactly the same way, so keep
them short.

### Running a program inside a job

Inside a batch script, use `srun` to run your program on the allocated
resources:

```sh
srun --hint=nomultithread --distribution=block:block ./my_program input.dat
```

* `--hint=nomultithread` tells Slurm to give each task a single physical
  core (use this unless your program was built for threaded MPI).
* `--distribution=block:block` puts consecutive tasks on the same node
  (better for memory-bound programs and for node-local I/O).

### Python environments

Do not install packages system-wide. Create your own environment in your
working directory:

```sh
module load python/3.11.7
python3 -m venv ~/myenv
source ~/myenv/bin/activate
pip install numpy pandas
```

Activate it again in every new shell (and in every batch script, by adding
`source ~/myenv/bin/activate` after the `#SBATCH` lines).

### Moving files between your laptop and Cirrus

The alias from step 2 works here too:

```sh
rsync -avP ./my_data cirrus:/epccfs/<project>/<project>/<username>/my_data/
rsync -avP cirrus:/epccfs/<project>/<project>/<username>/results/ ./results/
```

(`scp file cirrus:...` works as well, but `rsync` is better for large
transfers because it only sends what is new.)

---

## 9. Using FabSim3 and Cirrus

*This section is optional — skip it if the workshop only uses plain Cirrus.*

[FabSim3](https://github.com/djgroen/FabSim3) is the automation toolkit used
in this project: it writes the job script, copies your input files to the
remote machine, submits the job and collects the results. The workflow itself
is documented in the FabSim3 documentation — read that first, then apply it to
Cirrus.

### 9.1 FabSim3 documentation

| You want to | Go to |
|---|---|
| Install FabSim3, create the virtual environment, install an application, configure resources, run ensembles, collect results, troubleshoot | **[QCG Pilot-Job on Remote Machines](qcg_pilot.md)** — the most complete walk-through, and it applies to any SLURM machine |
| Install FabSim3 itself | [Installation guide](installation.md) (Windows/WSL: [Windows installation guide](windows_installation_guide.md)) |
| All Cirrus-specific settings: paths, partitions, batch headers, virtual environment | [Remote Machine Configuration → Notes for the Cirrus supercomputer](remote_machine_configuration.md) |
| Set up the SSH connection and multiplex the MFA login | [Multiplex Setup → Multiplexing for Cirrus](multiplex_setup.md) |
| Available plugins (FabFlee, FabDummy, ...) | [Plugins](plugins.md) |
| A worked example with the dummy plugin | [FabDummy Installation Test](fabdummy_installation_test.md) |
| The documentation online | <https://fabsim3.readthedocs.io> |
| Source code, issues and questions | <https://github.com/djgroen/FabSim3> and its [issue tracker](https://github.com/djgroen/FabSim3/issues) |

### 9.2 The three Cirrus-specific settings

Everything in the FabSim3 documentation applies as it is, except for three
things, which are specific to Cirrus:

**1. The machine block.** FabSim3 needs to know your username and project.
Add a `cirrus` block to `fabsim/deploy/machines_user.yml` in your FabSim3
installation:

```yaml
cirrus:
  username: <your-username>
  budget: <your-project>
  project: <your-project>
  remote: cirrus
  partition_name: standard
  qos_name: standard
  job_wall_time: 0-02:00:00
  home_path_template: /epccfs/$project/$project/$username
  work_path_template: /epccfs/$project/$project/$username/FabSim
  runtime_path_template: /epccfs/$project/$project/$username/FabSim
  manual_ssh: true
```

**2. The virtual environment.** FabSim3 creates it in the home path of the
machine, which on Cirrus is under `/epccfs` (see
[Remote Machine Configuration](remote_machine_configuration.md)):

```sh
fabsim cirrus create_virtual_env
```

**3. The batch header.** Cirrus offers two, and the choice affects what you
are charged for:

* `slurm-cirrus` (default) — shares nodes, you pay only for the cores you
  request. Use this for single-node jobs.
* `slurm-cirrus-exclusive` — reserves whole nodes, and is required for
  multi-node jobs (see section 7.2).

### 9.3 Try it

With the background connection from step 4 active, the quickest way to check
that everything is wired up is the dummy plugin, as described in the
[FabDummy Installation Test](fabdummy_installation_test.md):

```sh
fabsim cirrus stat                       # what is running on Cirrus?
fabsim cirrus dummy:dummy_test           # submit a small test job
fabsim cirrus fetch_results              # collect the results
```

From there, follow the FabSim3 documentation for the plugin you need — the
[Plugins](plugins.md) page lists what is available, and
[QCG Pilot-Job on Remote Machines](qcg_pilot.md) shows how to run many jobs
at once.

!!! tip
        FabSim3 makes many SSH calls in a row. Without the multiplexed
        connection from step 4 you would have to type your one-time code for
        every single one of them.

---

## 10. Troubleshooting

The Cirrus-specific messages are listed first; the FabSim3 rows at the
end point at the FabSim3 documentation.

| Message | What it means | What to do |
|---|---|---|
| `Permission denied (publickey,keyboard-interactive)` | Your key was not accepted, or the one-time code was wrong or expired | Check the key is registered with EPCC; retry the code (they change every 30 seconds); check `~/.ssh/config` has `User <your-username>` |
| `module: command not found` | `module` is only defined in a login shell | Use `bash -lc "module load ..."`, or `#!/bin/bash --login` in a script |
| `sbatch: error: Batch job submission failed: Invalid job name` | The job name is longer than the site limit (128 characters on Cirrus) | Shorten `--job-name` (FabSim3 truncates job names to 15 characters itself) |
| `sbatch: error: Job rejected: Nodes specified but the --exclusive flag is not specifed` | More than one node without `--exclusive` | Add `--exclusive`, or use a single node |
| `sbatch: error: Batch job submission failed: Unable to contact slurm controller` | The machine is busy or rebooting | Wait a minute and try again |
| Job stays `PD` with `ReqNodeNotAvail` | No node available right now | Nothing to fix; wait, and keep `--time` short |
| Job stays `PD` with `Priority` | Your project is at its limit on running jobs | Cancel finished-but-unknown jobs; ask the organiser about your limits |
| `No space left on device` | You filled your storage quota | `du -sh /epccfs/<project>/<project>/<username>` and delete old files |
| Job fails immediately with `Read-only file system` | The job wrote to `/home` or `/work` | Write to `/epccfs/...` instead |
| `slurmstepd: error: Exceeded job memory limit` | Your job asked for more memory than the node has | Use the `highmem` partition, or use fewer tasks |
| Job reaches the time limit | The job ran longer than `--time` | Raise `--time` (within your QoS limit) or make the job shorter; the output written up to that point is still in the output file |
| `ssh cirrus` hangs with no output | Network hiccup, or the MFA prompt is waiting | Press Enter; check with `ssh -O check cirrus` |
| FabSim3 asks for the one-time code on every command | The multiplexed connection is not running, or it has expired | Run `ssh cirrus` once more, then `ssh -O check cirrus`; see [Multiplexing for Cirrus](multiplex_setup.md) |
| FabSim3 says the machine is `not configured in machines_user.yml` | There is no `cirrus` block in your `machines_user.yml` | Add it - see [section 9.2](#92-the-three-cirrus-specific-settings) |
| FabSim3 job fails with `No module named ...` | The application is not installed in the virtual environment | See [QCG Pilot-Job on Remote Machines -> Troubleshooting](qcg_pilot.md#troubleshooting) |

---

## 11. Cheat sheet

```sh
# --- connecting ---
ssh cirrus                          # log in (asks for key passphrase + one-time code)
ssh -O check cirrus                # is the background connection alive?
ssh -O exit cirrus                 # close the background connection
exit                               # leave Cirrus

# --- looking around ---
whoami ; hostname ; pwd            # who am I, where am I
sinfo                             # partitions and their state
sinfo -p standard                 # nodes of one partition
squeue -u $USER                   # my jobs
sacct -u $USER -S today           # my jobs today, with core usage
module avail python               # available software
module load python/3.11.7         # load software
df -h /epccfs                     # free space

# --- jobs ---
sbatch my_job.sh                  # submit
squeue -u $USER                   # check state
sacct -j <jobid> --format=JobID,State,Elapsed,AllocCPUS,ExitCode
cat my_job-<jobid>.out            # read stdout
cat my_job-<jobid>.err            # read stderr
scancel <jobid>                   # cancel
salloc --nodes=1 --time=00:30:00 # interactive session on a compute node

# --- files ---
cd /epccfs/<project>/<project>/<username>
du -sh .                          # space used
rsync -avP ./local cirrus:/epccfs/<project>/<project>/<username>/
```

---

## 12. Good practice

* **Always ask for what you need.** One core for one hour is 1 core-hour; a
  full node is 288. Cirrus is a national facility shared with many research
  groups, and unused allocations are wasted.
* **Always set `--time`.** It is your safety net: a job that crashes and
  restarts in a loop stops by itself.
* **Check what you are spending** with
  `sacct -u $USER -S today --format=JobID,JobName%20,Elapsed,AllocCPUS`.
* **Cancel jobs you no longer need** with `scancel <jobid>`.
* **Write output to `/epccfs`,** never to `/home` or `/work`.
* **Do not run anything heavy on the login node.** If your laptop is waiting on
  a result for 20 minutes, it is waiting for the queue, not for your laptop.

## Getting help

* **Cirrus itself** (accounts, access, the machine misbehaving): EPCC support
  at <helpdesk@epcc.ed.ac.uk>.
* **The workshop**: the organisers, for anything about accounts, project codes
  or allocations.
* **FabSim3**: the documentation at <https://fabsim3.readthedocs.io>, the
  source code and the
  [issue tracker](https://github.com/djgroen/FabSim3/issues) at
  <https://github.com/djgroen/FabSim3>.
