# FabSim3 Plugins

### Installing plugins

By default, FabSim3 comes with the [FabDummy](https://github.com/djgroen/FabDummy) plugin, which is available in `~/FabSim3/plugins`. 

Other plugins can be installed in FabSim3, and are listed in `fabsim/deploy/plugins.yml` file.

* To install a specific plugin, simply type:
	```sh
	fabsim localhost install_plugin:<plug_name>
	```

* To install plugin from a *specific* github branch, you can use `branch` keyword
	```sh
	fabsim localhost install_plugin:<plug_name>,branch=<branch_name>
	```

### Updating plugins

Plugins can be updated by traversing into their respective base directory and running `git pull`. This is the recommended way to update plugins.

Alternatively, users can ``update'' plugins by rerunning `install_plugin`.

### Modifying plugins

Each plugin directory is its own GitHub repository, so users are able to modify their plugin when they go to `plugins/<name_of_their_plugin>`, e.g. to add new shared configurations or to define new automated FabSim3 tasks.

From there, they can push to GitHub as normal.

### List of available FabSim3 plugins

#### FabChemShell

FabChemShell is a ChemShell plugin for FabSim3.

* FabChemShell github repository : [:octicons-mark-github-16:](https://github.com/gh3orghiu/FabChemShell)
* FabChemShell documentation : [:fontawesome-solid-book:](https://github.com/gh3orghiu/FabChemShell/blob/master/README.md)


#### FabCovid19

FabCovid19 is a FabSim3 plugin for Flu And Coronavirus Simulator ([FACS](https://facs.readthedocs.io/en/latest/)).

* FabCovid19 github repository : [:octicons-mark-github-16:](https://github.com/djgroen/FabCovid19)
* FabCovid19 documentation : [:fontawesome-solid-book:](https://github.com/djgroen/FabCovid19/blob/master/README.md)


#### FabCovidsim

FabCovidsim is a FabSim3/EasyVVUQ plugin for [COVID-19 CovidSim microsimulation model](https://github.com/mrc-ide/covid-sim) developed Imperial College, London.

* FabCovidsim github repository : [:octicons-mark-github-16:](https://github.com/arabnejad/FabCovidsim)
* FabCovidsim documentation : [:fontawesome-solid-book:](https://github.com/arabnejad/FabCovidsim/blob/dev/README.md)


#### FabDummy

FabDummy is a dummy example plugin for FabSim3. It is meant to showcase a minimal implementation for a FabSim3 plugin.

* FabDummy github repository : [:octicons-mark-github-16:](https://github.com/djgroen/FabDummy)
* FabDummy documentation : [:fontawesome-solid-book:](https://github.com/djgroen/FabDummy/blob/master/README.md)

#### FabDynamics

FabDynamics is a plugin for [Dynamics](https://dynamics.readthedocs.io/en/latest/index.html) which is used for analysis of ODE systems.

* FabDynamics github repository : [:octicons-mark-github-16:](https://github.com/arindamsaha1507/dynamics)
* FabDynamics documentation : [:fontawesome-solid-book:](https://github.com/arindamsaha1507/FabDynamics/blob/main/README.md)


#### FabFlee

FabFlee is a plugin for automated [Flee](https://github.com/djgroen/flee) agent-based simulations. It provides an environment to construct, modify and execute simulations as a single run or ensemble runs. FabFlee aims to predict the distribution of incoming refugees across destination camps under a range of different policy situations.

* FabFlee github repository : [:octicons-mark-github-16:](https://github.com/djgroen/FabFlee)
* FabFlee documentation : [:fontawesome-solid-book:](https://github.com/djgroen/FabFlee/blob/master/doc/FabFlee.md)


#### FabMD

FabMD is a FabSim3 plugin for automated [LAMMPS](https://lammps.sandia.gov/)-based simulations.

This plugin provides functionality to extend FabSim3's workflow and remote submission capabilities to LAMMPS specific tasks.

* FabMD github repository : [:octicons-mark-github-16:](https://github.com/UCL-CCS/FabMD)
* FabMD documentation : [:fontawesome-solid-book:](https://fabmd.readthedocs.io)


#### FabMUSCLE

FabMUSCLE is a preliminary launcher for the MUSCLE3 toolkit. It serves to automatically set up [MUSCLE3](https://muscle3.readthedocs.io) simulations, launch the manager and its submodels, and keep all the associated data organized.

* FabMUSCLE github repository : [:octicons-mark-github-16:](https://github.com/djgroen/FabMUSCLE)
* FabMUSCLE documentation : [:fontawesome-solid-book:](https://github.com/djgroen/FabMUSCLE/blob/master/README.md)


#### FabParticleDA

FabParticleDA is a FabSim3 plugin for [ParticleDA.jl](https://github.com/Team-RADDISH/ParticleDA.jl)).

* FabParticleDA github repository : [:octicons-mark-github-16:](https://github.com/djgroen/FabParticleDA)
* FabParticleDA documentation : [:fontawesome-solid-book:](https://github.com/djgroen/FabParticleDA/blob/master/README.md)


#### FabSMD

FabSMD is a Steered Molecular Dynamics (SMD) plugin for FabSim3.

* FabSMD github repository : [:octicons-mark-github-16:](https://github.com/potterton48/FabSMD)
* FabSMD documentation : [:fontawesome-solid-book:](https://github.com/potterton48/FabSMD/blob/master/README.md)


#### FabUQCampaign

FabUQCampaign is a FabSim3 plugin for a climate modelling. It used to run an ensemble of [EasyVVUQ](https://github.com/UCL-CCS/EasyVVUQ/) samples on HPC resources.


* FabUQCampaign github repository : [:octicons-mark-github-16:](https://github.com/wedeling/FabUQCampaign)
* FabUQCampaign documentation : [:fontawesome-solid-book:](https://github.com/wedeling/FabUQCampaign/blob/master/README.md)
	* FabUQCampaign 2D ocean model documentation : [:fontawesome-solid-book:](https://github.com/wedeling/FabUQCampaign/blob/master/Tutorial_ocean.md)


#### FabNESO

FabNESO is a FabSim3 plugin for [Neptune Exploratory SOftware (NESO)](https://github.com/ExCALIBUR-NEPTUNE/NESO). 
It can be used to run both single instances and ensemble runs of NESO simulations.

* FabNESO github repository : [:octicons-mark-github-16:](https://github.com/UCL/FabNESO)
* FabNESO documentation : [:fontawesome-solid-book:](https://github.com/UCL/FabNESO/blob/main/README.md)
