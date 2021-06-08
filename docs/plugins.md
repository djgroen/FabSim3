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


### List of available FabSim3 plugins

#### FabFlee

FabFlee is a plugin for automated [Flee](https://github.com/djgroen/flee) agent-based simulations. It provides an environment to construct, modify and execute simulations as a single run or ensemble runs. FabFlee aims to predict the distribution of incoming refugees across destination camps under a range of different policy situations.

* FabFlee github repository : [:octicons-mark-github-16:](https://github.com/djgroen/FabFlee)
* FabFlee documentation : [:fontawesome-solid-book:](https://github.com/djgroen/FabFlee/blob/master/doc/FabFlee.md)


#### FabMD

FabMD is a FabSim3 plugin for automated [LAMMPS](https://lammps.sandia.gov/)-based simulations.

This plugin provides functionality to extend FabSim3's workflow and remote submission capabilities to LAMMPS specific tasks.

* FabMD github repository : [:octicons-mark-github-16:](https://github.com/UCL-CCS/FabMD)
* FabMD documentation : [:fontawesome-solid-book:](https://fabmd.readthedocs.io)


#### FabDummy

FabDummy is a dummy example plugin for FabSim3. It is meant to showcase a minimal implementation for a FabSim3 plugin.

* FabDummy github repository : [:octicons-mark-github-16:](https://github.com/djgroen/FabDummy)
* FabDummy documentation : [:fontawesome-solid-book:](https://github.com/djgroen/FabDummy/blob/master/README.md)


#### FabUQCampaign

FabUQCampaign is a FabSim3 plugin for a climate modelling. It used to run an ensemble of [EasyVVUQ](https://github.com/UCL-CCS/EasyVVUQ/) samples on HPC resources.


* FabUQCampaign github repository : [:octicons-mark-github-16:](https://github.com/wedeling/FabUQCampaign)
* FabUQCampaign documentation : [:fontawesome-solid-book:](https://github.com/wedeling/FabUQCampaign/blob/master/README.md)
	* FabUQCampaign 2D ocean model documentation : [:fontawesome-solid-book:](https://github.com/wedeling/FabUQCampaign/blob/master/Tutorial_ocean.md)



#### FabMUSCLE

FabMUSCLE is a preliminary launcher for the MUSCLE3 toolkit. It serves to automatically set up [MUSCLE3](https://muscle3.readthedocs.io) simulations, launch the manager and its submodels, and keep all the associated data organized.

* FabMUSCLE github repository : [:octicons-mark-github-16:](https://github.com/djgroen/FabMUSCLE)
* FabMUSCLE documentation : [:fontawesome-solid-book:](https://github.com/djgroen/FabMUSCLE/blob/master/README.md)


#### FabCovid19

FabCovid19 is a FabSim3 plugin for Flu And Coronavirus Simulator ([FACS](https://facs.readthedocs.io/en/latest/)).

* FabCovid19 github repository : [:octicons-mark-github-16:](https://github.com/djgroen/FabCovid19)
* FabCovid19 documentation : [:fontawesome-solid-book:](https://github.com/djgroen/FabCovid19/blob/master/README.md)


#### FabCovidsim

FabCovidsim is a FabSim3/EasyVVUQ plugin for [COVID-19 CovidSim microsimulation model](https://github.com/mrc-ide/covid-sim) developed Imperial College, London.

* FabCovidsim github repository : [:octicons-mark-github-16:](https://github.com/arabnejad/FabCovidsim)
* FabCovidsim documentation : [:fontawesome-solid-book:](https://github.com/arabnejad/FabCovidsim/blob/dev/README.md)



#### FabSMD

FabSMD is a Steered Molecular Dynamics (SMD) plugin for FabSim3.

* FabSMD github repository : [:octicons-mark-github-16:](https://github.com/potterton48/FabSMD)
* FabSMD documentation : [:fontawesome-solid-book:](https://github.com/potterton48/FabSMD/blob/master/README.md)


#### FabChemShell

FabChemShell is a ChemShell plugin for FabSim3.

* FabChemShell github repository : [:octicons-mark-github-16:](https://github.com/gh3orghiu/FabChemShell)
* FabChemShell documentation : [:fontawesome-solid-book:](https://github.com/gh3orghiu/FabChemShell/blob/master/README.md)



### FabDummy testing on localhost

#### FabDummy Plugin Installation
Open a terminal, and simply type:
```sh
fabsim localhost install_plugin:FabDummy
```
!!! info
	FabDummy plugin will be downloaded under `FabSim3/plugins/FabDummy`.

#### Testing
1. To run a dummy job, type:
```sh
fabsim localhost dummy:dummy_test
```
2. To run an ensemble of dummy jobs, type:
```sh
fabsim localhost dummy_ensemble:dummy_test
```
3. For both cases, i.e. a single dummy job or an ensemble of dummy jobs, you can fetch the results by using:
```sh
fabsim localhost fetch_results
```

For more advanced testing features, please refer to the FabDummy tutorial at <https://github.com/djgroen/FabDummy/blob/master/README.md>.

