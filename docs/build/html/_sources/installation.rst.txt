.. _installation:

.. Installation and Testing
.. ========================

Dependencies
============

1. FabSim3 requires the following Python modules 
    - PyYAML (any version) 
    - fabric3 (1.1.13.post1 has worked for us)
    - numpy
    - ruamel.yaml

    .. note:: You **ONLY** need to install `ruamel.yaml <https://pypi.org/project/ruamel.yaml>`_ package, others will be installed by FabSim3.
        To install that python package, simply type
        ::

            pip3 install ruamel.yaml


2. To perform the ``Py.test`` tests (not required for using FabSim3, but essential for running the tests), you will need `pytest <https://docs.pytest.org/en/latest/getting-started.html>`_ and `pytest-pep8 <https://pypi.org/project/pytest-pep8>`_.


3. To install FabSim3 plugins, **git** needs to be installed in your machine. 

Installing FabSim3
==================

1. Clone the code from the GitHub repository.


    .. code:: console

            git clone https://github.com/djgroen/FabSim3.git


2. To install **all** packages automatically and configure yml files, please got to your FabSim3 directory, and type

    .. code:: console

            python3 configure_fabsim.py



    .. note :: During this installation process, you will be asked for your local machine **password** for installation the required packages.


        
3. After installation process, the main FabSim3 directory is **added** in your ``$PYTHONPATH`` and ``$PATH`` environment variable. You can find these changes on your bash profile (for linux check ``~/.bashrc``, and for MacOS check ``~/.bash_profile``)


4. To make the **fabsim** command available in you system, please restart the shell by opening a new terminal or just re-load your bash profile by ``source`` command.

    .. code:: console

            [Linux machines] source ~/.bashrc
            [MacOS machines] source ~/.bash_profile






Updating FabSim3
================

If you have already installed FabSim3 and want to update to the latest version, in your local FabSim3 directory simply type ``git pull``

    Your personal settings like the ``machines_user.yml`` will be unchanged by this.

    .. Hint :: To update plugins you will have to **git pull** from within each plugin directory as and when required.


Known Issues
============

Here is the list of known issue that reported by our users so far:


ssh: connect to host localhost port 22: Connection refused
------------------------------------------------------------------

Linux
~~~~~
    This is a common issue on linux system, and it will be solved by **re-installing** ``openssh`` server, to do that

        1. Remove SSH with the following command

        .. code:: console

                sudo apt-get remove openssh-client openssh-server

        2. Install SSH again with

        .. code:: console

                sudo apt-get install openssh-client openssh-server

MacOS
~~~~~
    on Mac OSX, make sure turn on **Remote Login** under **System Preferences** then **File Sharing**.

    .. image:: images/ssh_macos_error.png
       :width: 300
       :align: center


The easiest way to test FabSim3 is to simply go to the base directory of your FabSim3 installation and try the examples below.

Mac users may get a 
``ssh: connect to host localhost port 22: Connection refused`` error. This means you must enable remote login. This is done in ``System Preferences > Sharing > Remote Login``.

List available commands
=======================

Simply type::

    fabsim -l


