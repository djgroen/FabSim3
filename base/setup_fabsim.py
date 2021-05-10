from deploy.templates import *
from deploy.machines import *
from fabric.contrib.project import *
from os import path, rename
import random
import string


@task
def install_plugin(name, branch=None):
    """
    Install a specific FabSim3 plugin.
    """
    config = yaml.load(open(path.join(env.localroot,
                                      'deploy',
                                      'plugins.yml')
                            ),
                       Loader=yaml.SafeLoader
                       )
    info = config[name]
    plugin_dir = "%s/plugins" % (env.localroot)

    # check if the requested pluging is already installed or not
    # if it is already installed, rename the current pluging directory and
    # warn user
    print("plugin_dir = {}".format(plugin_dir))
    print("check dir : {}/{}".format(plugin_dir, name))
    if path.exists("{}/{}".format(plugin_dir, name)):
        # generating random strings
        N = 5
        res = "".join(random.choices(string.ascii_uppercase +
                                     string.digits, k=N))
        rename(
            "{}/{}".format(plugin_dir, name),
            "{}/{}_{}".format(plugin_dir, name, res)
        )
        print_msg_box(
            title="WARNNING",
            msg="The {} plugin directory is already exists\n"
            "To keep your previous folder, we rename it to : {}_{}".format(
                name, name, res)
        )

    local("mkdir -p %s" % (plugin_dir))
    local("rm -rf %s/%s" % (plugin_dir, name))

    if branch is None:
        local("git clone %s %s/%s" % (info["repository"],
                                      plugin_dir,
                                      name)
              )
    else:
        local("git clone --branch %s %s %s/%s" % (branch,
                                                  info["repository"],
                                                  plugin_dir,
                                                  name)
              )


@task
def avail_plugin():
    """
    print list of available plugins.
    """
    config = yaml.load(open(path.join(env.localroot,
                                      'deploy',
                                      'plugins.yml')
                            ),
                       Loader=yaml.SafeLoader
                       )
    print("\nList of available plugins\n")
    print("%-20s %s" % ('plugin name', 'repository'))
    print("%-20s %s" % ('-----------', '----------'))
    for name, repo in config.items():
        print("%-20s %s" % (name, repo['repository']))


@task
def update_plugin(name):
    """
    Update a specific FabSim3 plugin.
    """
    plugin_dir = "%s/plugins" % (env.localroot)
    local("cd %s/%s && git pull" % (plugin_dir, name))


@task
def remove_plugin(name):
    """
    Remove the specified plug-in.
    """
    config = yaml.load(
        open(path.join(env.localroot, 'deploy', 'plugins.yml')),
        Loader=yaml.SafeLoader
    )
    plugin_dir = '{}/plugins'.format(env.localroot)
    local('rm -rf {}/{}'.format(plugin_dir, name))


def add_local_paths(module_name):
    # This variable encodes the default location for templates.
    env.local_templates_path.insert(
        0, "$localroot/plugins/%s/templates" % (module_name)
    )
    # This variable encodes the default location for blackbox scripts.
    env.local_blackbox_path.insert(
        0, "$localroot/plugins/%s/blackbox" % (module_name)
    )
    # This variable encodes the default location for Python scripts.
    env.local_python_path.insert(
        0, "$localroot/plugins/%s/python" % (module_name)
    )
    # This variable encodes the default location for config files.
    env.local_config_file_path.insert(
        0, "$localroot/plugins/%s/config_files" % (module_name)
    )


def get_setup_fabsim_dirs_string():
    """
    Returns the commands required to set up the fabric directories. This
    is not in the env, because modifying this is likely to break FabSim
    in most cases. This is stored in an individual function, so that the
    string can be appended in existing commands, reducing the
    performance overhead.
    """
    return(
        'mkdir -p $config_path; mkdir -p $results_path; mkdir -p $scripts_path'
    )


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
    print("""To set up your SSH keys, you will be logged in to your
          local machine once using SSH. You may be asked to provide
          your password once to facilitate this login.""")

    if path.isfile("%s/.ssh/id_rsa.pub" % (path.expanduser("~"))):
        print("local id_rsa key already exists.")
    else:
        local(
            "ssh-keygen -q -f %s/.ssh/id_rsa -t rsa -b 4096 -N \"%s\"" %
            (path.expanduser("~"), password)
        )
    local(template("ssh-copy-id -i ~/.ssh/id_rsa.pub %s 2>ssh_copy_id.log"
                   % env.host_string))


@task
def setup_fabsim(password=""):
    """
    Combined command which sets up both the SSH keys and creates the
    FabSim directories.
    """
    setup_ssh_keys(password)
    setup_fabsim_dirs()
    # FabSim3 ships with FabDummy by default,
    # to provide a placeholder example for a plugin.
    install_plugin("FabDummy")


@task
def bash_machine_alias(name=None):
    if name is None:
        print("Error: the bash alias name (argument 'name') is not set.")
        print("the correct format is :")
        print("\t\t\t fab %s bash_alias:<prefered_ash_alias_name>\n" %
              (env.machine_name))
        exit()

    if name == 'fabsim':
        print("Error: cannot set a machine alias to 'fabsim', as this will")
        print("overwrite the main fabsim command.")
        exit()

    destname = path.join(env.localroot, 'bin', name)
    content = script_template_content('bash_alias')

    # save the file
    target = open(destname, 'w')
    target.write(content)
    target.close()
    # change file permission to be executable
    local("chmod u+x %s" % (destname))

    print("the alias name is set. so, you can use :\n")
    print("\t\t\t %s ..." % (name))
    print("\tinstead of :")
    print("\t\t\t fab %s ..." % (env.machine_name))
    print("\n\nNote: you need to reload your bashrc file or restart " +
          "the shell to use the new alias name")
