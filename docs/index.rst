.. FabSim3 documentation master file, created by
   sphinx-quickstart on Fri Jun  7 11:11:04 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: ../logo.jpg

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

FabSim3 is publicly available at: http://www.github.com/djgroen/FabSim3 The
accompanying software paper can be found here:
https://doi.org/10.1016/j.cpc.2016.05.020

The main plugins for FabSim3 include:

* FabMD, focused on molecular dynamics.
* FabFlee, focused on agent-based modelling.
* FabUQCampaign, focused on UQ ensemble sampling.
* FabDummy, a dummy plugin used for testing the toolkit.
* FabMUSCLE, a preliminary integration with the MUSCLE3 coupling toolkit.


Key reference documents
=======================
Here's a list of particularly useful reference documents for FabSim3.

**Basic:**

* Basic installation and testing instructions: https://github.com/djgroen/FabSim3/docs/installation.rst
* Testing simple jobs with FabDummy: https://github.com/djgroen/FabDummy/blob/master/README.md
* How to set up and use FabSim3 with the Singularity containerization environment: https://github.com/djgroen/FabSim3/blob/master/doc/FabSim3SingularityUsage.md

**Intermediate:**

* You can find detailed tutorials for FabMD (molecular dynamics) here: https://github.com/UCL-CCS/FabMD/blob/master/doc
* Do UQ with a coupled agent-based migration model using the FabFlee plugin: https://github.com/djgroen/FabFlee/blob/master/doc/Tutorial.md

**Advanced:**

* How to create your own plugin: https://github.com/djgroen/FabSim3/blob/master/doc/CreatePlugins.md
* How to write automation scripts: https://github.com/djgroen/FabSim3/blob/master/doc/CreateAutomationScripts.md
* How to use FabSim with QCG middleware: https://github.com/djgroen/FabSim3/blob/master/doc/FabSim%2BQCG.md

Citing FabSim3
==============

Please find the BibTex reference below of our FabSim3 software paper in *Computer Physics Communications*::


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

.. _toc:

Table of contents
-----------------

.. toctree::
   :maxdepth: 2

   installation


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
