# -*- coding: utf-8 -*-
#
# This source file is part of the FabSim software toolkit, which is distributed
# under the BSD 3-Clause license.
# Please refer to LICENSE for detailed information regarding the licensing.
#
# This file contains functions which help parse and process
# machine-specific definitions, written in machines*.yml

import site
import os
# import fabric.api
# from fabric.api import prefix,cd,execute
from fabric.api import env
# from fabric.api import task
from fabric.utils import _AliasDict
import sys
import posixpath
import yaml
from .templates import *
from functools import *
from pprint import pprint, pformat
from rich.console import Console
from rich import print
from rich.panel import Panel
from pprint import pprint

from fabric.api import task as fabric_task

# here, I have to use this approach, decorating the fabric task with dummy
# decorator in order to load the functions (tagged by @task) to be loaded
# by mkdocstring. This fix the mkdocstring issue without has any effecting on
# on fabric @task functionality :)


def new_task_decorator(func):
    @fabric_task
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


task = new_task_decorator


# If we're running in an activated virtualenv, use that.
if "VIRTUAL_ENV" in os.environ:
    virtual_env = os.path.join(
        os.environ.get("VIRTUAL_ENV"),
        "lib",
        "python%d.%d" % sys.version_info[:2],
        "site-packages",
    )
    site.addsitedir(virtual_env)
    print("Using Virtualenv =>", virtual_env)
del site

# Root of local FabSim installation
work_dir = os.path.dirname(os.path.abspath(__file__))
env.localroot = os.path.dirname(os.path.dirname(work_dir))
env.fabsim_root = os.path.dirname(work_dir)
env.localhome = os.path.expanduser("~")
# dict containing local paths to all plugins.
env.localplugins = {}
env.no_ssh = False
env.no_hg = False
# Load and invoke the default non-machine specific config JSON dictionaries.
config = yaml.load(
    open(os.path.join(env.fabsim_root, "deploy", "machines.yml")),
    Loader=yaml.SafeLoader,
)
env.update(config["default"])

try:
    user_config = yaml.load(
        open(os.path.join(env.fabsim_root, "deploy", "machines_user.yml")),
        Loader=yaml.SafeLoader,
    )
except FileNotFoundError:
    print("There is not machines_user.yml under fabsim/deploy folder!!!\n")
    user_config = yaml.load(
        open(os.path.join(env.fabsim_root, "deploy",
                          "machines_user_example.yml")),
        Loader=yaml.SafeLoader,
    )


env.update(user_config["default"])
env.verbose = False
env.needs_tarballs = False
env.pather = posixpath
env.remote = None
env.node_type = None
env.dollar = "$"
env.machine_name = None
env.node_type_restriction = ""
env.node_type_restriction_template = ""
# Maximum number of characters permitted in the name of a job
# in the queue system
# -1 for unlimited
env.max_job_name_chars = None
env.lammps_exec = "undefined"
run_prefix_commands = env.run_prefix_commands[:]
if env.temp_path_template:
    env.temp_path = template(env.temp_path_template)

env.pythonroot = os.path.join(env.fabsim_root, "python")
env.blackboxroot = os.path.join(env.fabsim_root, "blackbox")
env.replicas = 1
env.colorize_errors = True


def generate_module_commands(script=None):
    """
    Generates the required module commands for the remote machine scripts.
    It reads the `modules` env variables defined in machine yaml files.
    Example input entry:
    ```yaml
    modules:
        # list of modules to be loaded on remote machine
        loaded: ["python/3.7.3", "openmpi/4.0.0_gcc620"]
        # list of modules to be unloaded on remote machine
        unloaded: ["python"]

    ```
    and generates these lines in the job script
    ```sh
    # unload modules
    module unload python
    # load required modules
    module load python python/3.7.3 openmpi/4.0.0_gcc620
    ```
    """
    module_commands = [
        "module {}".format(module) for module in env.modules["all"]
    ]

    module_commands += [
        "module {}".format(module)
        for module in env.modules.get("nonexistent", "")
    ]

    module_commands += [
        "module unload {}".format(module)
        for module in env.modules.get("unloaded", "")
    ]
    module_commands += [
        "module load {}".format(module)
        for module in env.modules.get("loaded", "")
    ]
    if script is not None:
        module_commands += [
            "module {}".format(module)
            for module in env.modules.get(script, "")
        ]
    return module_commands


module_commands = generate_module_commands()
env.run_prefix = (
    " \n".join(module_commands + list(map(template, run_prefix_commands)))
    or "echo THE FIRST Running..."
)

if (
    not any(
        "install_app" in str or "install_packages" in str for str in env.tasks
    )
    and hasattr(env, "venv")
    and str(env.venv).lower() == "true"
):
    # since we are going to load python VirtualEnv, so, it would be better
    # to unload any current loaded python modules, in order to avoid
    # conflicts during the execution of python program
    env.run_prefix += (
        "\n# load python from VirtualEnv"
        "\nmodule unload python\n"
        "source {}/bin/activate".format(env.virtual_env_path)
    )


@task
def machine(name):
    """
    Load the machine-specific configurations.
    Completes additional paths and interpolates them, via
    `complete_environment`.
    Usage, e.g. `fab machine:hector build`

    Args:
        name (str): the name of remote machine
    """
    if "import" in config[name]:
        # Config for this machine is based on another
        env.update(config[config[name]["import"]])

        if config[name]["import"] in user_config:
            env.update(user_config[config[name]["import"]])

    env.update(config[name])
    if name in user_config:
        env.update(user_config[name])
    env.machine_name = name

    # Construct modules environment: update, not replace when overrides are
    # done.
    env.modules = config["default"]["modules"]
    if "import" in config[name]:
        env.modules.update(config[config[name]["import"]].modules)
    env.modules.update(config[name].get("modules", {}))

    if "import" in config[name]:
        if config[name]["import"] in user_config:
            env.modules.update(user_config[config[name]["import"]].modules)

    env.modules.update(user_config[name].get("modules", {}))

    complete_environment()


@task
def print_machine_config_info(name):
    """
    Print the `env` configuration variables for the input remote machine name

    Example Usage:
    ```sh
    fabsim localhost print_machine_config_info:<machine_name>
    ```

    Args:
        name (str, optional): the remote machine name
    """
    print(
        Panel(
            pformat(config[name]),
            title="[green1]Defaults[/green1]",
            expand=False,
        )
    )
    print(
        Panel(
            pformat(user_config[name]),
            title="[red1]User overrides[/red1]",
            expand=False,
        )
    )


# Metaprogram the machine wrappers
for machine_name in set(config.keys()) - set(["default"]):

    globals()[machine_name] = fabric_task(alias=machine_name)(
        partial(machine, machine_name)
    )
    # globals()[machine_name] = task(alias=machine_name)(
    #     partial(machine, machine_name)
    # )


def load_plugin_env_vars(plugin_name):
    """
    the decorator to load the `env` variable specific for the pluing
    To use this decorator, you need to add it to the `#!python @task` function
    in your plugin.
    example :
    ```python
    @task
    @load_plugin_env_vars("<plugin_name>")
    def function_name(...):
        ...
        ...
    ```

    Args:
        plugin_name (str): the plugin name
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(
                "calling task {} from plugin {}".format(
                    func.__name__, plugin_name
                )
            )
            add_plugin_environment_variable(plugin_name)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def add_plugin_environment_variable(plugin_name):
    """
    read the plugin machine specific configuration for the input plugin name.

    !!! info
        the plugin machine specific config file should follow the following
        name structure:
        ```sh
        machines_<plugin_name>_user.yml
        ```

    Args:
        plugin_name (str): the name of pluing

    """
    # machines_<plugin>.yml
    # machines_<plugin>_user.yml
    plugin_path = os.path.join(env.localroot, "plugins", plugin_name)
    machine_name = env.machine_name
    plugin_machines_user = os.path.join(
        plugin_path, "machines_{}_user.yml".format(plugin_name)
    )

    if not os.path.isfile(plugin_machines_user):
        return

    plugin_config = yaml.load(
        open(plugin_machines_user), Loader=yaml.SafeLoader
    )

    user_config.update(plugin_config)
    # only update environment variable based on plugin_machines_user yaml file
    old_env = my_deepcopy(env)
    if "import" in config[machine_name]:
        if config[machine_name]["import"] in plugin_config:
            env.update(plugin_config[config[machine_name]["import"]])

    if "default" in plugin_config and plugin_config["default"] is not None:
        env.update(plugin_config["default"])

    if (
        machine_name in plugin_config
        and plugin_config[machine_name] is not None
    ):
        env.update(plugin_config[machine_name])

    env.modules = config["default"]["modules"]
    if "import" in config[machine_name]:
        if config[machine_name]["import"] in plugin_config:
            env.modules.update(
                plugin_config[config[machine_name]["import"]].modules
            )

    if (
        machine_name in plugin_config
        and plugin_config[machine_name] is not None
    ):
        env.modules.update(plugin_config[machine_name].get("modules", {}))
    else:
        error_msg = "{} is not available in {}".format(
            machine_name, plugin_machines_user
        )
        error_msg += "\nor there is no item for that machine name"
        print(
            Panel(
                "[red1]{}[/red1]".format(error_msg),
                title="[yellow1]Error[/yellow1]",
                expand=False,
            )
        )

    complete_environment()
    msg = "\n".join(findDiff(env, old_env, path="env"))
    title = "New/Updated environment variables from {} plugin".format(
        plugin_name
    )
    print(
        Panel(
            "{}".format(msg),
            title="[yellow1]{}[/yellow1]".format(title),
            expand=False,
        )
    )


def complete_environment():
    """
    Add paths to the environment based on information in the yaml configs
    files.

    Environment vars created can be used in job-script templates:

    - `results_path`: Path to store results
    - `remote_path` : Root of area for checkout and build on remote
    - `config_path` : Path to store config files
    - `scripts_path` : Path where job-queue-submission scripts generated by
        Fabric are sent.
    - `run_prefix` : Command string to invoke before any job is run.
    """
    env.hosts = ["{}@{}".format(env.username, env.remote)]
    env.host_string = "{}@{}".format(env.username, env.remote)
    env.home_path = template(env.home_path_template)
    env.runtime_path = template(env.runtime_path_template)
    env.work_path = template(env.work_path_template)
    env.remote_path = template(env.remote_path_template)
    env.stat = template(env.stat)
    env.results_path = env.pather.join(env.work_path, "results")
    env.config_path = env.pather.join(env.work_path, "config_files")
    env.scripts_path = env.pather.join(env.work_path, "scripts")
    env.local_results = os.path.expanduser(template(env.local_results))

    if hasattr(env, "flee_location"):
        env.flee_location = template(env.flee_location)

    for i in range(0, len(env.local_templates_path)):
        env.local_templates_path[i] = os.path.expanduser(
            template(env.local_templates_path[i])
        )

    for i in range(0, len(env.local_config_file_path)):
        env.local_config_file_path[i] = os.path.expanduser(
            template(env.local_config_file_path[i])
        )

    # module_commands = generate_module_commands()
    module_commands = generate_module_commands(script=env.get("script", None))
    run_prefix_commands = env.run_prefix_commands[:]
    env.run_prefix = (
        " \n".join(
            module_commands
            + list(map(template, map(template, run_prefix_commands)))
        )
        or "/bin/true || true"
    )
    # This echo is commented because can cause problem for slurmID saving
    # or 'echo The Running...'

    if env.temp_path_template:
        env.temp_path = template(env.temp_path_template)

    if hasattr(env, "virtual_env_path") and env.virtual_env_path:
        env.virtual_env_path = template(env.virtual_env_path)

    if hasattr(env, "app_repository") and env.app_repository:
        env.app_repository = template(env.app_repository)

    if (
        not any(
            "install_app" in str or "install_packages" in str
            for str in env.tasks
        )
        and hasattr(env, "venv")
        and str(env.venv).lower() == "true"
    ):
        # since we are going to load python VirtualEnv, so, it would be better
        # to unload any current loaded python modules, in order to avoid
        # conflicts during the execution of python program
        env.run_prefix += (
            "\n# load python from VirtualEnv"
            "\nmodule unload python\n"
            "source {}/bin/activate".format(env.virtual_env_path)
        )


# complete_environment()


def my_deepcopy(obj):
    new_obj = {}
    for key in obj:
        if type(obj[key]) in [dict, _AliasDict]:
            new_obj[key] = my_deepcopy(obj[key])
        elif isinstance(obj[key], (list)):
            new_obj[key] = obj[key][:]
        else:
            new_obj[key] = obj[key]
    return new_obj


def findDiff(d1, d2, path=""):
    ret_str = []
    for key in d1:
        if key not in d2:
            ret_str.append("{} :".format(path))
            ret_str.append("  +++ {} is a new added key".format(key))
        else:
            if type(d1[key]) in [dict, _AliasDict]:
                if path == "":
                    nested_path = key
                else:
                    nested_path = path + "->" + key
                ret_str += findDiff(d1[key], d2[key], nested_path)
            elif isinstance(d1[key], (bool, str, int)):
                if d1[key] != d2[key]:
                    ret_str.append("{} :".format(path))
                    ret_str.append("  --- {} : {}".format(key, str(d2[key])))
                    ret_str.append("  +++ {} : {}".format(key, str(d1[key])))
                else:
                    pass
            elif isinstance(d1[key], (list)):
                if set(d1[key]) != set(d2[key]):
                    ret_str.append("{} :".format(path))
                    ret_str.append("  --- {} : {}".format(key, str(d2[key])))
                    ret_str.append("  +++ {} : {}".format(key, str(d1[key])))

    return ret_str
