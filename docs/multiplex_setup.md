### Setting up multiplexing
This document briefly details how user/developers can set up multiplexing

#### Step 1

Create a local file named `~/.ssh/config`, or append to it.

In this file, you need the following block
```sh
Host archer2
   User <archer2-username>
   HostName login.archer2.ac.uk
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
archer2:
  username: <username>
  remote: archer2
  manual_ssh: true
  project: <project>
  budget: <budget>
```

