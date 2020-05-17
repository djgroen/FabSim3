.. _plugins:


Installing plugins
==================

By default, FabSim3 comes with the `FabDummy <https://github.com/djgroen/FabDummy>`__ plugin installed. Other plugins can be installed, and are listed in  ``deploy/plugins.yml``.

    * To install a specific plugin, simply type:: 

        fabsim localhost install_plugin:<plug_name>


Creating a new plugin
=====================

To create a new plugin for FabSim3:

1. Fork the `FabDummy <https://www.github.com/djgroen/FabDummy>`__ repository.
2. Rename the repository, and modify it to suit your own needs as you see fit.
3. Rename **FabDummy.py** to the **<name of your plugin>.py**.
4. In your new plugin repository, at the top of the **<name of your plugin>.py**, change ``add_local_paths("FabDummy")`` to ``add_local_paths(<name of your plugin>)``.
5. In the **main** `FabSim3 <https://github.com/djgroen/FabSim3>`__ repository, add an entry for your new plugin in ``deploy/plugins.yml``.
6. Set up your plugin using ::
    
    fab localhost install_plugin:<name of your plugin>

7. You're good to go, although you'll inevitably will have to debug some of your modifications made in the second step of course.

Examples
--------
	For examples, see the plugins available in ``deploy/plugins.yml``. `FabDummy <https://github.com/djgroen/FabDummy>`__ and `FabMD <https://github.com/UCL-CCS/FabMD>`_ are particularly good examples to investigate.


FabDummy testing on the local host
===================================

Plugin Installation
-------------------
	Open a terminal, and simply type::

	        fabsim localhost install_plugin:FabDummy


	.. Note:: **FabDummy** plugin will be downloaded under ``<fabsim home folder>/plugins/FabDummy``


Testing
-------
	1. To run a dummy job, type::

	    fabsim localhost dummy:dummy_test
	    
	2. To run an ensemble of dummy jobs, type::

	    fabsim localhost dummy_ensemble:dummy_test
	    
	3. for both cases, i.e., a single dummy job or an ensemble of dummy jobs, you can fetch the results by using::

	    fabsim localhost fetch_results

	For more advanced testing features, please refer to the FabDummy tutorial at https://github.com/djgroen/FabDummy/blob/master/README.md.


LAMMPS testing on the local host
================================

Dependencies and Pre-Configurations
-----------------------------------
	1. Install LAMMPS (see http://lammps.sandia.gov) for detailed download and installation instructions).

	2. Modify ``machines_user.yml`` to make the **lammps_exec** variable point to the location of the LAMMPS executable. e.g.
	    
	.. code-block:: yaml
			
			localhost:
				lammps_exec: "/home/james/bin/lmp_serial"
			
		    	    
	3. FabSim3 contains sample LAMMPS input files, so there's no need to download that.


Plugin Installation
-------------------

	Before run LAMMPS test data set, you should install FabMD which provides functionality to extend FabSim3's workflow and remote submission capabilities to LAMMPS specific tasks. Please install it by typing::

		  	  fabsim localhost install_plugin:FabMD


Testing
-------

	1. Run the LAMMPS test data set using:: 
	    
	    fabsim localhost lammps_dummy:lammps_dummy,cores=1,wall_time=1:00:0
	    
	2. Run the following command to copy the output of your job in the results directory. By default this will be a subdirectory in ``<FabSim3 folder>/results``::

	    fabsim localhost fetch_results