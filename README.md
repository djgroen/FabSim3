FabSim
======

FabSim is a Python-based automation toolkit for scientific simulation and data processing workflows. It aims to enable users to perform remote tasks from a local command-line, and to run applications while curating the environment variables and the input and output data in a systematic manner. To provide that curation, FabSim uses a basic data transfer functionalities such as rsync and ssh. 

FabSim also contains a system for defining machine-specific configurations, including templates to execute jobs through schedulers such as PBSPro and SGE. These machine-specific configurations are stored in the repository, apply to all applications run on that machine, and can be updated by any contributor who feels that a fix or improvement is required.

FabSim relies strongly on Fabric (http://www.fabfile.org, shown to work with versions 1.5.3 and 1.10.0) and PyYAML. Previous versions of FabSim (most notably FabHemeLB and FabMD) have been used to run simulation workflows on machines such as ARCHER, SuperMUC, Legion (the UCL supercomputer), as well as local clusters and desktops.

Features which I hope to implement in the near future are:
* Better documentation and testing examples.
* Support for ensemble job submissions with block-job or array-job mechanisms (either directly through the scheduler or through RADICAL Cybertools).
* Support for GSISSH.

FabSim is now publicly available (as early-stage software) at: http://www.github.com/djgroen/FabSim

Earlier derivative versions of FabSim include:
* FabHemeLB (previously known as FabricHemeLB), which is used to automate workflows involving 
the HemeLB lattice-Boltzmann simulation environment (see http://www.github.com/UCL/hemelb for 
the source code of that).
* FabMD, which is used to semi-automatically coarse-grain polymer systems.

The aim for our work on FabSim is to create a generalized version of these two toolkits, and for this toolkit to be aplied to other applications as well.

## Installation and usage 

For instructions on how to install and test FabSim, please refer to `INSTALL.md`.
