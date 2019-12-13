.. _createplugin:

Creating a new plugin
=====================

To create a new plugin for FabSim3:

1. Fork the `FabDummy <https://www.github.com/djgroen/FabDummy>`_ repository.
2. Rename the repository, and modify it to suit your own needs as you see fit.
3. Rename **FabDummy.py** to the **<name of your plugin>.py**.
4. In your new plugin repository, at the top of the **<name of your plugin>.py**, change ``add_local_paths("FabDummy")`` to ``add_local_paths(<name of your plugin>)``.
5. In the **main** `FabSim3 <https://github.com/djgroen/FabSim3>`_ repository, add an entry for your new plugin in ``deploy/plugins.yml``.
6. Set up your plugin using ::

    fab localhost install_plugin:<name of your plugin>
    
7. You're good to go, although you'll inevitably will have to debug some of your modifications made in the second step of course.

Examples
--------
For examples, see the plugins available in ``deploy/plugins.yml``. `FabDummy <https://github.com/djgroen/FabDummy>`_ and `FabMD <https://github.com/UCL-CCS/FabMD>`_ are particularly good examples to investigate.
