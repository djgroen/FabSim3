# Install an application remotely from your laptop to the cluster

## Basic informations

In machine.yml or machine_user.yml, the 'app_repository' variable must be set on the remote you want to install the application. 
'app_repository' is the path of the repository, on the remote, that will contain the sources of the application and its dependencies. 

All the information about the application has to be define in deploy/application.yml like below :

> QCG-PilotJob:
>	repository: https://github.com/vecma-project/QCG-PilotJob.git   # github repository
>	name : QCGPilotManager  # Name of the downloaded zip with pip  
>	version: 0.1	# last release version
>   additional_dependencies:   # Additional package you'd like to install 
>        - numpy
>        - pandas 

The application will be install to the '--user' path by default.

You can also choose to use a virtualenvironment to install your application.
Variable `virtual_env_path` in machine.yml set the path to the virtual environment, if it does not exist, the virtual env is created.
To specify this option, you must set `virtual_env=True` in the fabsim command.


## Examples 

fab genji install_app:QCG-PilotJob

fab qcg install_app:QCG-PilotJob,virtual_env=True

An installation script will be created and stored on the remote in the following directory :
    ~/Fabsim3/scripts


Will install PilotJobManager on Genji supercomputer 


Warning: Currently, it only works with python application.
