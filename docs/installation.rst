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


2. To install **all** packages automatically and configure yml files, please go to your FabSim3 directory, and type

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


FileNotFoundError: [Errno 2] No such file or directory: 'fab': 'fab'
--------------------------------------------------------------------
It is possible that your python bin path directory is not in the system ``PATH``. You may see a ``WARNING`` message during the FabSim3 installation (by executing ``python3 configure_fabsim.py`` command). Here an example :

.. code:: console

      WARNING: The script fab is installed in '<---->/Python/3.<xxx>/bin' which is not on PATH.
      Consider adding this directory to PATH or, 
      if you prefer to suppress this warning, use --no-warn-script-location.

      Traceback (most recent call last):
      File "configure_fabsim.py", line 189, in <module>
        main()
      File "configure_fabsim.py", line 148, in main
        cwd=FS3_env.FabSim3_PATH) == 0
      File "<---->/python3..<xxx>/subprocess.py", line 339, in call
        with Popen(*popenargs, **kwargs) as p:
      File "<---->/python3..<xxx>/subprocess.py", line 800, in __init__
        restore_signals, start_new_session)
      File "<---->/python3..<xxx>/subprocess.py", line 1551, in _execute_child
        raise child_exception_type(errno_num, err_msg, err_filename)
    FileNotFoundError: [Errno 2] No such file or directory: 'fab': 'fab'


To fix this issue, you need to add the executable path of ``fab`` to your system ``PATH`` environment variable. To make this update permanent, please to to you ``bash`` file which could be ``.bash_profile``, ``.bashrc``, or ``.zshrc`` depends on your OS and shell version, and add these line at the end. Please make sure that you used the same executable path for ``fab`` as it mentioned in the warning message


.. code:: bash

    export PATH=$PATH:<fab_executable_PATH>



.. note :: If you are having a problem which is not listed here, please raise a `github issue <https://github.com/djgroen/FabSim3/issues/new/choose>`_ in FabSim3 repository, and provide a full output log, so we can have a look and make a suggestions.


List available commands
=======================

Simply type::

    fabsim -l


