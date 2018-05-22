from deploy.templates import *
from deploy.machines import *
from fabric.contrib.project import *

def get_setup_fabsim_dirs_string():
    """
    Returns the commands required to set up the fabric directories. This is not in the env, because modifying this
    is likely to break FabSim in most cases.
    This is stored in an individual function, so that the string can be appended in existing commands, reducing
    the performance overhead.
    """
    return 'mkdir -p $config_path; mkdir -p $results_path; mkdir -p $scripts_path'

@task
def setup_fabsim_dirs(name=''):
    """
    Sets up directories required for the use of FabSim.
    """
    """
    Creates the necessary fab dirs remotely.
    """
    run(template(get_setup_fabsim_dirs_string()))

@task
def setup_ssh_keys(password=""):
    """
    Sets up SSH key pairs for FabSim access.
    """
    import os.path
    if os.path.isfile("%s/.ssh/id_rsa.pub" % (os.path.expanduser("~"))):
      print("local id_rsa key already exists.")
    else:
      local("ssh-keygen -q -f %s/.ssh/id_rsa -t rsa -b 4096 -N \"%s\"" % (os.path.expanduser("~"), password))
    local(template("ssh-copy-id -i ~/.ssh/id_rsa.pub %s" % env.host_string))

@task
def setup_fabsim(password=""):
    setup_ssh_keys(password)
    setup_fabsim_dirs()


