### Setting up multiplexing
This document briefly details how user/developers can set up multiplexing.
Multiplexing is a reasonably secure way to reduce the number of times that
users have to type passwords when connecting to remote resources.


### Multiplexing for the local host.
This section describes how to set up multiplexing for the local host.

#### Step 1

Create a local file named `~/.ssh/config`, or append to it.

In this file, you need the following block
```sh
Host lh
   User <your-local-username>
   HostName localhost
   ControlPath ~/.ssh/controlmasters/%r@%h:%p
   ControlMaster auto
   ControlPersist 30m
```

!!! note
        The duration of ControlPersist can be modified to suit your needs. Note however that shorter durations are more secure.

#### Step 2

Create a directory using `mkdir ~/.ssh/controlmasters`

#### Step 3

Modify your existing `machines_user.yml` file such that it contains the following:

```yml
localhost:
  username: <username>
  remote: lh
  manual_ssh: true
```


### Multiplexing for remote HPC
This section describes how to set up multiplexing for a remote machine. 
The documentation uses the ARCHER2 supercomputer as an example.

ARCHER2 requires multi-factor authentication (MFA): your SSH key **plus** a
one-time passcode (TOTP). Multiplexing lets you complete the MFA prompt only
once, after which FabSim3 reuses the authenticated connection instead of
prompting on every SSH call.

#### Step 1

Create a local file named `~/.ssh/config`, or append to it.

In this file, you need the following block
```sh
Host archer2
   User <archer2-username>
   HostName login.archer2.ac.uk
   ForwardAgent yes
   ServerAliveInterval 60
   ControlPath ~/.ssh/control-%r@%h:%p
   ControlMaster auto
   ControlPersist 12h
```

!!! note
        The duration of ControlPersist can be modified to suit your needs. Note however that shorter durations are more secure.

#### Step 2

Establish the master connection once, completing the MFA prompt when asked:

```sh
ssh archer2
```

You can `exit` as soon as you are logged in; the master connection stays
alive in the background for the duration set by `ControlPersist`. Verify it
is running with:

```sh
ssh -O check archer2
```

All subsequent FabSim3 commands (e.g. `fabsim archer2 ...`) then reuse this
connection and will not prompt for the passcode again.

!!! note
        When `ControlPersist` expires, or the master connection is closed, run `ssh archer2` again to re-authenticate before using FabSim3.

#### Step 3

Modify your existing `machines_user.yml` file such that it contains the following:

```yml
archer2:
  username: <username>
  remote: archer2
  manual_ssh: true
  project: <project>
  budget: <budget>   # SLURM account, e.g. "<project>-<username>" (note the hyphen)
```

