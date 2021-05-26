from fabsim.deploy.templates import *
from fabsim.deploy.machines import *
from fabric.contrib.project import *
from fabric.api import local, run
from os import path, rename
import random
import string
from pprint import pprint
from rich.console import Console
from rich.table import Column, Table
from rich import print
from rich.panel import Panel


@task
def install_plugin(plugin_name, branch=None):
    """
    Install a specific FabSim3 plugin.

    Args:
        plugin_name (str): plugin name
        branch (str, optional): branch name
    """
    config = yaml.load(
        open(path.join(env.fabsim_root, "deploy", "plugins.yml")),
        Loader=yaml.SafeLoader,
    )
    info = config[plugin_name]

    plugin_dir = path.join(env.localroot, "plugins")

    # check if the requested pluging is already installed or not
    # if it is already installed, rename the current pluging directory and
    # warn user
    if path.exists("{}/{}".format(plugin_dir, plugin_name)):
        # generating random strings
        N = 5
        res = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=N)
        )
        rename(
            "{}/{}".format(plugin_dir, plugin_name),
            "{}/{}_{}".format(plugin_dir, plugin_name, res),
        )
        print(
            Panel(
                "[red1]The {} plugin directory is already exists.\n"
                "To keep your previous folder, we rename it to[/red1] : "
                "[green1]{}_{}[/green1]".format(plugin_name, plugin_name, res),
                title="[yellow1]WARNING[/yellow1]",
                expand=False,
            )
        )

    local("mkdir -p {}".format(plugin_dir))
    local("rm -rf {}/{}".format(plugin_dir, plugin_name))

    if branch is None:
        local(
            "git clone {} {}/{}".format(
                info["repository"], plugin_dir, plugin_name
            )
        )
    else:
        local(
            "git clone --branch {} {} {}/{}".format(
                branch, info["repository"], plugin_dir, plugin_name
            )
        )


@task
def avail_plugin():
    """
    print list of available plugins.
    """
    config = yaml.load(
        open(path.join(env.fabsim_root, "deploy", "plugins.yml")),
        Loader=yaml.SafeLoader,
    )
    table = Table(
        title="\nList of available plugins",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("plugin name")
    table.add_column("repository")
    for plugin_name, repo in config.items():
        table.add_row(
            "[blue]{}[/blue]".format(plugin_name),
            "{}".format(repo["repository"]),
        )
    print(table)


@task
def update_plugin(plugin_name):
    """
    Update a specific FabSim3 plugin.

    Args:
        plugin_name (str): plugin name
    """
    plugin_dir = "{}/plugins".format(env.fabsim_root)
    local("cd {}/{} && git pull".format(plugin_dir, plugin_name))


@task
def remove_plugin(name):
    """
    Remove the specified plug-in.

    Args:
        name (str): plugin name
    """
    config = yaml.load(
        open(path.join(env.fabsim_root, "deploy", "plugins.yml")),
        Loader=yaml.SafeLoader,
    )
    plugin_dir = "{}/plugins".format(env.fabsim_root)
    local("rm -rf {}/{}".format(plugin_dir, name))


def add_local_paths(plugin_name):
    """
    Updates `env` variables for the input plugin name

    Args:
        plugin_name (str): plugin name
    """
    # This variable encodes the default location for templates.
    env.local_templates_path.insert(
        0, path.join(env.localroot, "plugins", plugin_name, "templates")
    )
    # This variable encodes the default location for blackbox scripts.
    env.local_blackbox_path.insert(
        0, path.join(env.localroot, "plugins", plugin_name, "blackbox")
    )
    # This variable encodes the default location for Python scripts.
    env.local_python_path.insert(
        0, path.join(env.localroot, "plugins", plugin_name, "python")
    )
    # This variable encodes the default location for config files.
    env.local_config_file_path.insert(
        0, path.join(env.localroot, "plugins", plugin_name, "config_files")
    )


def get_setup_fabsim_dirs_string():
    """
    Returns the commands required to set up the fabric directories. This
    is not in the env, because modifying this is likely to break FabSim
    in most cases. This is stored in an individual function, so that the
    string can be appended in existing commands, reducing the
    performance overhead.
    """
    return (
        "mkdir -p $config_path; "
        "mkdir -p $results_path; "
        "mkdir -p $scripts_path"
    )


@task
def setup_fabsim_dirs():
    """
    Sets up directories required for the use of FabSim.
    """
    run(template(get_setup_fabsim_dirs_string()))


@task
def setup_ssh_keys(password=""):
    """
    Sets up SSH key pairs for FabSim access.
    """
    print(
        Panel(
            "[magenta]To set up your SSH keys, you will be logged in to your\n"
            "local machine once using SSH. You may be asked to provide\n"
            "your password once to facilitate this login.[/magenta]",
            title="hamid",
            expand=False,
        )
    )

    if path.isfile("{}/.ssh/id_rsa.pub".format(path.expanduser("~"))):
        print("local id_rsa key already exists.")
    else:
        local(
            'ssh-keygen -q -f {}/.ssh/id_rsa -t rsa -b 4096 -N "{}"'.format(
                path.expanduser("~"), password
            )
        )
    local(
        template(
            "ssh-copy-id -i ~/.ssh/id_rsa.pub {} 2>ssh_copy_id.log".format(
                env.host_string
            )
        )
    )


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


# @task
# def bash_machine_alias(name=None):
#     if name is None:
#         print("Error: the bash alias name (argument 'name') is not set.")
#         print("the correct format is :")
#         print("\t\t\t fab %s bash_alias:<prefered_ash_alias_name>\n" %
#               (env.machine_name))
#         exit()

#     if name == 'fabsim':
#         print("Error: cannot set a machine alias to 'fabsim', as this will")
#         print("overwrite the main fabsim command.")
#         exit()

#     destname = path.join(env.fabsim_root, 'bin', name)
#     content = script_template_content('bash_alias')

#     # save the file
#     target = open(destname, 'w')
#     target.write(content)
#     target.close()
#     # change file permission to be executable
#     local("chmod u+x %s" % (destname))

#     print("the alias name is set. so, you can use :\n")
#     print("\t\t\t %s ..." % (name))
#     print("\tinstead of :")
#     print("\t\t\t fab %s ..." % (env.machine_name))
#     print("\n\nNote: you need to reload your bashrc file or restart " +
#           "the shell to use the new alias name")
