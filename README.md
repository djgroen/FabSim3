FabSim
======

[![Build Status](https://travis-ci.com/djgroen/FabSim3.svg?branch=fabsim_qcg_dev)](https://travis-ci.com/djgroen/FabSim3)
[![Docker Pulls](https://img.shields.io/docker/pulls/vecmafabsim3/fabsimdocker.svg)](https://hub.docker.com/r/vecmafabsim3/fabsimdocker/)
[![Docker Pulls](https://img.shields.io/docker/automated/vecmafabsim3/fabsimdocker.svg)](https://hub.docker.com/r/vecmafabsim3/fabsimdocker/)

<!---
for master branch use : 
[![Build Status](https://travis-ci.com/djgroen/FabSim3.svg?branch=master)](https://travis-ci.com/djgroen/FabSim3))

[![Dockerhub link](https://img.shields.io/badge/hosted-dockerhub-22b8eb.svg)](https://hub.docker.com/r/willprice/nvidia-ffmpeg/)

[![Singularity hub link](https://www.singularity-hub.org/static/img/hosted-singularity--hub-%23e32929.svg)](https://singularity-hub.org/collections/521)
-->

FabSim is a Python-based automation toolkit for scientific simulation and data processing workflows, licensed under the BSD 3-clause license. It aims to enable users to perform remote tasks from a local command-line, and to run applications while curating the environment variables and the input and output data in a systematic manner. To provide that curation, FabSim uses a basic data transfer functionalities such as rsync and ssh. 

FabSim also contains a system for defining machine-specific configurations, including templates to execute jobs through schedulers such as PBSPro, Loadleveller and SGE. These machine-specific configurations are stored in the repository, apply to all applications run on that machine, and can be updated by any contributor who feels that a fix or improvement is required.

FabSim relies strongly on Fabric (http://www.fabfile.org, shown to work with versions 1.5.3 and 1.10.0) and PyYAML. Previous versions of FabSim (most notably FabHemeLB and FabMD) have been used to run simulation workflows on machines such as ARCHER, SuperMUC, BlueJoule, as well as local clusters and desktops.

FabSim is now publicly available at: http://www.github.com/djgroen/FabSim
The accompanying software paper can be found here: https://doi.org/10.1016/j.cpc.2016.05.020

Derivative versions of FabSim include:
* FabHemeLB (previously known as _FabricHemeLB_), which is used to automate workflows involving 
the HemeLB lattice-Boltzmann simulation environment (see http://www.github.com/UCL/hemelb for 
the source code of that).
* FabMD, which is used to semi-automatically coarse-grain polymer systems (part of this repository).
* FabBioMD, which is used to facilitate protein-ligand binding affinity calculations (part of this repository).
* FabFlee, which is under development and used to automate agent-based simulations of forced migration.


## Installation and usage 

For instructions on how to install and test FabSim, please refer to `INSTALL.md`.

### Citing FabSim

Please find the BibTex reference below of our FabSim software paper in _Computer Physics Communications_:

```
@article{GROEN2016375,
title = "FabSim: Facilitating computational research through automation on large-scale and distributed e-infrastructures",
journal = "Computer Physics Communications",
volume = "207",
number = "Supplement C",
pages = "375 - 385",
year = "2016",
issn = "0010-4655",
doi = "https://doi.org/10.1016/j.cpc.2016.05.020",
url = "http://www.sciencedirect.com/science/article/pii/S0010465516301448",
author = "Derek Groen and Agastya P. Bhati and James Suter and James Hetherington and Stefan J. Zasada and Peter V. Coveney",
}
```
