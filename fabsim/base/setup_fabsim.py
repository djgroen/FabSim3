"""Module to install, update, and remove FabSim3 plugins."""

import random
import string
from os import path, rename

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from fabsim.base.decorators import task
from fabsim.base.env import env
from fabsim.base.networks import local, run
from fabsim.deploy.templates import template


def warn_duplicate_plugin(plugin_dir, plugin_name, random_string_length=5):
    """Warn user about the duplicate plugin directory."""

    res = "".join(
        random.choices(
            string.ascii_uppercase + string.digits, k=random_string_length
        )
    )
    rename(f"{plugin_dir}/{plugin_name}", f"{plugin_dir}/{plugin_name}_{res}")
    print("\n")
    console = Console()
    console.print(
        Panel(
            f"[orange_red1]The {plugin_name} "
            "plugin directory already exists.\n"
            "To keep your previous folder, we rename it to[/orange_red1]: "
            f"[dark_cyan]{plugin_name}_{res}[/dark_cyan]",
            title="[dark_cyan]WARNING[/dark_cyan]",
            expand=False,
        )
    )
    print("\n")


@task
def install_plugin(plugin_name, branch=None):
    """
    Install a specific FabSim3 plugin.

    Args:
        plugin_name (str): plugin name
        branch (str, optional): branch name
    """

    fname = path.join(env.fabsim_root, "deploy", "plugins.yml")
    with open(fname, encoding="utf-8") as file:
        config = yaml.load(file, Loader=yaml.SafeLoader)
    info = config[plugin_name]

    plugin_dir = path.join(env.localroot, "plugins")

    # check if the requested pluging is already installed or not
    # if it is already installed, rename the current pluging directory and
    # warn user
    if path.exists(f"{plugin_dir}/{plugin_name}"):
        warn_duplicate_plugin(plugin_dir, plugin_name)

    local(f"mkdir -p {plugin_dir}")
    local(f"rm -rf {plugin_dir}/{plugin_name}")

    if branch is None:
        local(f"git clone {info['repository']} '{plugin_dir}/{plugin_name}'")
    else:
        local(
            f"git clone --branch {branch} {info['repository']} "
            f"'{plugin_dir}/{plugin_name}'"
        )

    print(f"{plugin_name} plugin installed...")

    if path.exists(f"{plugin_dir}/{plugin_name}/requirements.txt"):
        print("Installing plugin requirements...")
        local(f"pip install -r {plugin_dir}/{plugin_name}/requirements.txt")
        print("Plugin requirements installed successfully.")
    else:
        print(f"No requirements.txt file found for {plugin_name} plugin")

    print(f"Plugin {plugin_name} installed successfully.")


@task
def avail_plugin():
    """
    print list of available plugins.
    """

    fname = path.join(env.fabsim_root, "deploy", "plugins.yml")
    with open(fname, encoding="utf-8") as file:
        config = yaml.load(file, Loader=yaml.SafeLoader)

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
            f"[blue]{plugin_name}[/blue]",
            f"{repo['repository']}",
            f"{installed}",
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
    plugin_dir = f"{env.localroot}/plugins"
    local(f"cd {plugin_dir}/{plugin_name} && git pull")


@task
def remove_plugin(name):
    """
    Remove the specified plug-in.

    Args:
        name (str): plugin name
    """
    plugin_dir = f"{env.localroot}/plugins".format()
    local(f"rm -rf {plugin_dir}/{name}")


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


def get_clean_fabsim_dirs_string(prefix):
    """
    Returns the commands required to clean the fabric directories. This
    is not in the env, because modifying this is likely to break FabSim
    in most cases. This is stored in an individual function, so that the
    string can be appended in existing commands, reducing the
    performance overhead.
    """
    return (
        f"rm -rf $config_path/{prefix}*; "
        f"rm -rf $results_path/{prefix}*; "
        f"rm -rf $scripts_path/{prefix}*"
    )


@task
def setup_fabsim_dirs():
    """
    Sets up directories required for the use of FabSim.
    """
    run(template(get_setup_fabsim_dirs_string()))


@task
def clean_fabsim_dirs(prefix=""):
    """
    Cleans up directories used by FabSim.
    """
    run(template(get_clean_fabsim_dirs_string(prefix)))


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

    home = path.expanduser("~")
    if path.isfile(f"{home}/.ssh/id_rsa.pub"):
        print("local id_rsa key already exists.")
    else:
        local(
            f'ssh-keygen -q -f {home}/.ssh/id_rsa'
            f' -t rsa -b 4096 -N "{password}"'
        )
    local(
        template(
            "ssh-copy-id -i ~/.ssh/id_rsa.pub "
            f"{env.host_string} 2>ssh_copy_id.log"
        )
    )
