# QCG Pilot Job installation on remote machines

QCG Pilot Job is a lightweight implementation of the Pilot Job mechanism which can be used to run a very large number of jobs efficiently on remote machines. We present the instructions to install QCG Pilot Job on remote machines.

## Prerequisites

The pre-requisites for installing QCG Pilot Job on a **remote machine** using **FabSim**, we essentially need
- FabSim installed on the local machine
- Access to the remote machine

## Installation

For the installation itself, install the following command from the terminal

```sh
fabsim <remote machine name> install_app:QCG-PilotJob,venv=True
```

Once the command is issued, the following steps will occur in sequence:
1. Miniconda will be installed locally.
2. All the dependencies required for installation of QCG Pilot Job will be installed locally
3. Prepares the script that when run on the remote machine will install QCG Pilot Job
4. Transfers all the dependencies to the remote machine
5. Submits the installation job script to the remote machine

Since, the number of dependencies for QCG Pilot Job is quite large, therefore, the command may take upto 45 minutes to run.

After all the above-mentioned processes are done, the status of the submitted job on the remote machine can be checked using

```sh
fabsim <remote machine name> stat
```

Once, the sumbitted job completes successfully, QCG Pilot Job will be installed on the remote machine.
