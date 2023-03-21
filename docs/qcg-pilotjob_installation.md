# QCG Pilot Job installation on remote machines

QCG Pilot Job is a lightweight implementation of the Pilot Job mechanism which
can be used to run a very large number of jobs efficiently on remote clusters and supercomputers.

More information on QCG-PilotJob can be found on their [ReadTheDocs site](https://qcg-pilotjob.readthedocs.io/en/develop/).

![images/qcg-pj.webp!](Image of a QCG Pilot Job container)
*Example of a QCG-Pilotjob container, which dynamically facilitates a diverse set of code executions within a single queuing system job. [Source](https://link.springer.com/chapter/10.1007/978-3-030-77977-1_39)*

Here we present how you can install QCG Pilot Job on remote machines, so that you can use it with FabSim3.

!!! note
    Note that FabSim3 can also work with a pre-installed version of QCG-PilotJob; but for those who need to set it up manually this document is meant to provide some help.

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
