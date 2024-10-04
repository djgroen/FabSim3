
# *An automation toolkit for complex simulation tasks*

<figure>
   <img src="images/logo.jpg" width="200"> 
</figure>


[![Run Tests](https://github.com/djgroen/FabSim3/actions/workflows/Pytests.yml/badge.svg?branch=master)](https://github.com/djgroen/FabSim3/actions/workflows/Pytests.yml)
[![Docker Pulls](https://img.shields.io/docker/pulls/vecmafabsim3/fabsimdocker.svg)](https://hub.docker.com/r/vecmafabsim3/fabsimdocker/)
[![Docker Pulls](https://img.shields.io/docker/automated/vecmafabsim3/fabsimdocker.svg)](https://hub.docker.com/r/vecmafabsim3/fabsimdocker/)
[![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/djgroen/FabSim3?style=flat)](https://github.com/djgroen/FabSim3/tags)
<!---
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/djgroen/FabSim3.svg?logo=lgtm&logoWidth=18)]
(https://lgtm.com/projects/g/djgroen/FabSim3/context:python)
-->
[![GitHub Issues](https://img.shields.io/github/issues/djgroen/FabSim3.svg)](https://github.com/djgroen/FabSim3/issues)
[![GitHub last-commit](https://img.shields.io/github/last-commit/djgroen/FabSim3.svg)](https://github.com/djgroen/FabSim3/commits/master)


FabSim3 is a Python-based automation toolkit for scientific simulation and data processing workflows, licensed under the BSD 3-clause license. It is developed as part of the SEAVEA project <http://www.seavea-project.org>, and is part of the VECMA Toolkit <http://www.vecma-toolkit.eu>.

Among other things, FabSim3 supports the use of simple one-liner commands to:


* Enable execution of simulation and analysis tasks on supercomputers.
* Establish and run coupled models using the workflow automation functionalities.
* Organize input, output and environment information, creating a consistent log and making it possible by default to repeat/reproduce runs.
* Perform large ensemble simulations (or replicated ones) using a one-liner command.

Users can perform complex remote tasks from a local command-line, and run single jobs, ensembles of multiple jobs, and dynamic workflows through schedulers such as SLURM, PBSPro, LoadLeveller and QCG. FabSim3 stores machine-specific configurations in the repository, and applies it to all applications run on that machine. These configurations are updated by any contributor who feels that a fix or improvement is required.

FabSim3 relies strongly on Fabric (<http://www.fabfile.org>, shown to work with versions 1.5.3 and 1.10.0) and PyYAML. It has been used to run simulation workflows on supercomputers such as ARCHER, SuperMUC, Carthesius, Eagle, as well as local clusters and desktops.


FabSim3 is publicly available at: <http://www.github.com/djgroen/FabSim3>. 

The accompanying software paper can be found here: <https://doi.org/10.1016/j.cpc.2022.108596>
There is also a paper about the original version of FabSim here: <https://doi.org/10.1016/j.cpc.2016.05.020>.

The main plugins for FabSim3 include:

* FabMD, focused on molecular dynamics.
* FabFlee, focused on agent-based modelling of human migration.
* FabCovid19: focused on agent-based modelling of infectious disease spread.
* FabUQCampaign, focused on UQ ensemble sampling.
* FabDummy, a dummy plugin used for testing the toolkit.
* FabMUSCLE, a preliminary integration with the MUSCLE3 coupling toolkit.
* FabNEPTUNE, a plugin specific for project NEPTUNE (on fusion research).
* FabParticleDA: a preliminary plugin for ParticleDA.jl
