import yaml
from os import path, rename
import random
import string
from fabsim.base.env import env
from fabsim.base.networks import local, run
from fabsim.base.decorators import task
from fabsim.deploy.templates import template
from rich.console import Console
from rich.table import Table
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
        print("\n")
        console = Console()
        console.print(
            Panel(
                "[orange_red1]The {} plugin directory is already exists.\n"
                "To keep your previous folder, we rename it to[/orange_red1]: "
                "[dark_cyan]{}_{}[/dark_cyan]".format(
                    plugin_name, plugin_name, res),
                title="[dark_cyan]WARNING[/dark_cyan]",
                expand=False,
            )
        )
        print("\n")

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

    print("{} plugin installed...".format(plugin_name))


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
    table.add_column("installed")
    for plugin_name, repo in config.items():
        if path.exists(path.join(env.localroot, "plugins", plugin_name)):
            installed = "\u2714"  # ✔
        else:
            installed = "\u2718"  # ✘
        table.add_row(
            "[blue]{}[/blue]".format(plugin_name),
            "{}".format(repo["repository"]),
            "{}".format(installed)
        )
    console = Console()
    console.print(table)


@task
def update_plugin(plugin_name):
    """
    Update a specific FabSim3 plugin.

    Args:
        plugin_name (str): plugin name
    """
    plugin_dir = "{}/plugins".format(env.localroot)
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
    plugin_dir = "{}/plugins".format(env.localroot)
    local("rm -rf {}/{}".format(plugin_dir, name))


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
    console = Console()
    console.print(
        Panel(
            "[magenta]To set up your SSH keys, you will be logged in to your\n"
            "local machine once using SSH. You may be asked to provide\n"
            "your password once to facilitate this login.[/magenta]",
            title="[dark_cyan]Setup SSH keys[/dark_cyan]",
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
