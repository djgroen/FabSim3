.. FabSim3 documentation master file, created by
   sphinx-quickstart on Thu May 14 01:06:45 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

An automation toolkit for complex simulation tasks
===========================================================

FabSim3 is a Python-based automation toolkit for scientific simulation and data
processing workflows, licensed under the BSD 3-clause license. It is developed 
as part of VECMA (http://www.vecma.eu), and is part of the VECMA Toolkit 
(http://www.vecma-toolkit.eu).

Among other things, FabSim3 supports the use of simple one-liner commands to:

* Enable execution of simulation and analysis tasks on supercomputers.
* Establish and run coupled models using the workflow automation functionalities.
* Organize input, output and environment information, creating a consistent log and making it possible by default to repeat/reproduce runs.
* Perform large ensemble simulations (or replicated ones) using a one-liner command.

Users can perform complex remote tasks from a local command-line, and 
run single jobs, ensembles of multiple jobs, and dynamic workflows through schedulers such as SLURM,
PBSPro, LoadLeveller and QCG. FabSim3 stores machine-specific configurations in the repository, and applies it to all
applications run on that machine. These configurations are updated by any
contributor who feels that a fix or improvement is required.

FabSim3 relies strongly on Fabric (http://www.fabfile.org, shown to work with
versions 1.5.3 and 1.10.0) and PyYAML. It has been used to run simulation
workflows on supercomputers such as ARCHER, SuperMUC, Carthesius, Eagle, as well
as local clusters and desktops.

FabSim3 is publicly available at: http://www.github.com/djgroen/FabSim3 
The accompanying software paper can be found here:
https://doi.org/10.1016/j.cpc.2016.05.020

The main plugins for FabSim3 include:

* FabMD, focused on molecular dynamics.
* FabFlee, focused on agent-based modelling.
* FabUQCampaign, focused on UQ ensemble sampling.
* FabDummy, a dummy plugin used for testing the toolkit.
* FabMUSCLE, a preliminary integration with the MUSCLE3 coupling toolkit.


.. toctree::
   :caption: Installation and Testing
   :maxdepth: 1

   installation

.. toctree::
   :caption: Plugins
   :maxdepth: 1

   plugins


.. toctree::
   :caption: Advanced Topics
   :maxdepth: 1

   createautomation


.. toctree::
   :caption: Remote Machine Configuration
   :maxdepth: 1

   remotemachineconfig

.. toctree::
   :caption: Containerized versions
   :maxdepth: 1
   
   containerizedversion
   fabsim3qcg



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

