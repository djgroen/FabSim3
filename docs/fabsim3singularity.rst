.. _fabsim3singularity:

FabSim3 Singularity Usage
=========================

In this tutorial, we will explain how to download, setup, and run `FabSim3 <https://github.com/djgroen/FabSim3>`_ within a singularity container image.

Dependencies
------------
* `Singularity <https://www.sylabs.io>`_, which you can download and install from `here <https://www.sylabs.io/guides/3.0/user-guide/installation.html>`_.

* `OpenSSH Server <https://www.openssh.com/>`_:

Installation under Ubuntu Linux::
    
        sudo apt install openssh-server
    
Installations under CentOS Linux::
        
        sudo yum install -y openssh-server

Installation
-------------
1. Download the singularity image from `Singularity Hub <https://singularity-hub.org/>`_::

    singularity pull --name fabsim.simg shub://arabnejad/FabSim3
	
.. note:: The download image should be kept as ``fabsim.simg``, this filename will be used later for setting environment variable and alias names in your ``bashrc`` file

2. To see How to Use Fabsim3 singularity::

    ./fabsim.simg --help

or

    ``./fabsim.simg -h``

3. Running the following will download the `FabSim3 <https://github.com/djgroen/FabSim3>`_ library in your local machine::

    ./fabsim.simg --install [fabsim_INSTALL_DIR]
    
or

    ``./fabsim.simg -i [fabsim_INSTALL_DIR]``

By default, it will be downloaded in sub-folder ``FabSim3`` in your current directory, you also can set the installation directory by setting ``[fabsim_INSTALL_DIR]`` parameter.

4. At the end of installation part, you will received a message, which explain how you should setup your PC for further usage::

    ./fabsim.simg -i [fabsim_INSTALL_DIR]

Please add/load the generated ``fabsim_env.conf`` in your ``~/.bashrc``. 

To load::

    $ source \${fabsim_INSTALL_DIR}/fabsim_env.conf 

To add to your ``~/.bashrc``::
    
    $ echo \"source \${fabsim_INSTALL_DIR}/fabsim_env.conf\" >> ~/.bashrc 	
    $ source ~/.bashrc 	
    
``fabsim_INSTALL_DIR`` will be replaced by your local machine path

5. After, loading the environment variable from ``fabsim_env.conf`` into your into the current shell script, **fab** command will be available as a alias name to run for singularity image and accept all FabSim3 command.

6. For `QCG <http://www.qoscosgrid.org/trac/qcg>`_ users, 

* Please make sure, you udpate/replace ``username: "plg<your-username>"`` with your username account in

    ``{fabsim_INSTALL_DIR}/deploy/machines_user.yml``

* Sets up SSH key pairs for FabSim3 access:: 
    
    fab qcg setup_ssh_keys

* Please create a **globus** in your **$HOME** directory, If Not Exist:: 

    mkdir -p ~/.globus
    
* Copy ``usercert.pem`` and ``userkey.pem`` from your account to ``~/.globus``::

    scp plg<user>@eagle.man.poznan.pl:~/.globus/usercert.pem ~/.globus
    scp plg<user>@eagle.man.poznan.pl:~/.globus/userkey.pem ~/.globus
		
FabSim3 Usage
-------------
To enable use of FabSim3 on your local host, type the following command and, then you can use all FabSim3 commands::

    fab localhost setup_fabsim
