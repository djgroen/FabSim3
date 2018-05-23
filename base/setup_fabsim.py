from deploy.templates import *
from deploy.machines import *
from fabric.contrib.project import *

import fileinput
import sys

def activate_plugin(name):
    found = False
    fabfile_loc = "%s/fabfile.py" % (env.localroot)

    for line in fileinput.input(fabfile_loc, inplace=1):
        if name in line:
            found = True
            if line[0] == "#":
                line = line[1:]
        sys.stdout.write(line)

    # if the commented pattern is not found, then we need to append a new import at the end of fabfile.py.
    if found == False:
        with open(fabfile_loc, "a") as myfile:
            myfile.write("from deploy.%s.%s import *\n" % (name, name))

#TODO: Make general purpose plugin install command.
@task
def install_FabMD():
    with cd("%s/deploy" % env.localroot):
        local("rm -rf FabMD")
        local("git clone git@github.com:UCL-CCS/FabMD.git")
        activate_plugin("FabMD")

def add_local_paths(module_name):
    # This variable encodes the default location for templates.
    env.local_templates_path.insert(0, "$localroot/deploy/%s/templates" % (module_name))
    # This variable encodes the default location for blackbox scripts.
    env.local_blackbox_path.insert(0, "$localroot/deploy/%s/blackbox" % (module_name))
    # This variable encodes the default location for Python scripts.
    env.local_python_path.insert(0, "$localroot/deploy/%s/python" % (module_name))

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
    """
    Combined command which sets up both the SSH keys and creates the FabSim directories.
    """
    setup_ssh_keys(password)
    setup_fabsim_dirs()


