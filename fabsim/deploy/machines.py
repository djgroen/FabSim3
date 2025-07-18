import importlib
import inspect
import os
import sys
import time
from pprint import pformat, pprint

import yaml
from beartype import beartype
from beartype.typing import Dict, List, Optional
from rich.console import Console
from rich.panel import Panel

from fabsim.base.decorators import task
from fabsim.base.env import env
from fabsim.base.utils import add_print_prefix
from fabsim.deploy.templates import template

config = yaml.safe_load(
    open(os.path.join(env.fabsim_root, "deploy", "machines.yml"))
)
# Include private machines
config_file_private = os.path.join(
    env.fabsim_root, "deploy", "machines_private.yml"
)
if os.path.isfile(config_file_private):
    config_private = yaml.safe_load(
        open(config_file_private)
    )
    config |= config_private

env.update(config["default"])

try:
    user_config = yaml.safe_load(
        open(os.path.join(env.fabsim_root, "deploy", "machines_user.yml"))
    )
except FileNotFoundError:
    # raise FileNotFoundError(
    #     "There is NO machines_user.yml under fabsim/deploy directory!!!\n"
    # )
    print("There is not machines_user.yml under fabsim/deploy folder!!!\n")
    user_config = yaml.safe_load(
        open(
            os.path.join(
                env.fabsim_root, "deploy", "machines_user_example.yml"
            )
        )
    )
env.update(user_config["default"])


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
run_prefix_commands = env.run_prefix_commands[:]
env.run_prefix = (
    " \n".join(module_commands + list(map(template, run_prefix_commands)))
    or "echo THE FIRST Running..."
)


@beartype
def load_machine(machine_name: str) -> None:
    """
    Load the machine-specific configurations.
    Completes additional paths and interpolates them, via
    `complete_environment`.
    """
    # Check if the machine exists in config before proceeding
    if machine_name not in config:
        raise ValueError(
            f'The requested remote machine "{machine_name}" is not '
            "listed in `machines.yml`. It cannot be used as a host.\n"
            f"Available remote machines are: {list(config.keys())}"
        )

    # If the machine exists in `config`, proceed with loading
    if "import" in config[machine_name]:
        # Config for this machine is based on another
        env.update(config[config[machine_name]["import"]])

        if config[machine_name]["import"] in user_config:
            env.update(user_config[config[machine_name]["import"]])

    env.update(config[machine_name])

    # Check if the machine exists in `user_config`
    if machine_name in user_config:
        env.update(user_config[machine_name])
    else:
        # Raise a descriptive error if it's missing in `machines_user.yml`
        raise ValueError(
            f'"{machine_name}" is listed in `machines.yml` but is not '
            'configured in `machines_user.yml`. Please add it before using it.'
        )

    env.machine_name = machine_name

    # Construct modules environment, not replace when overrides are done
    env.modules = config["default"]["modules"]
    if "import" in config[machine_name]:
        env.modules.update(config[config[machine_name]["import"]].modules)
    env.modules.update(config[machine_name].get("modules", {}))

    if "import" in config[machine_name]:
        if config[machine_name]["import"] in user_config:
            env.modules.update(
                user_config[config[machine_name]["import"]].modules
            )

    # Add modules from user_config if available
    if machine_name in user_config:
        env.modules.update(user_config[machine_name].get("modules", {}))

    complete_environment()


def complete_environment() -> None:
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
    env.host_string = "{}@{}".format(env.username, env.remote)
    env.home_path = template(env.home_path_template)
    env.runtime_path = template(env.runtime_path_template)
    env.work_path = template(env.work_path_template)
    env.remote_path = template(env.remote_path_template)
    env.stat = template(env.stat)
    env.results_path = os.path.join(env.work_path, "results")
    env.config_path = os.path.join(env.work_path, "config_files")
    env.scripts_path = os.path.join(env.work_path, "scripts")
    env.local_results = os.path.expanduser(template(env.local_results))
    env.local_system_time = int(time.time())

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
        or "true"
    )

    if env.temp_path_template:
        env.temp_path = template(env.temp_path_template)

    if hasattr(env, "virtual_env_path") and env.virtual_env_path:
        env.virtual_env_path = template(env.virtual_env_path)

    if hasattr(env, "app_repository") and env.app_repository:
        env.app_repository = template(env.app_repository)

    if (
        # not any(
        #     "install_app" in str or "install_packages" in str
        #     for str in env.tasks
        # )
        env.task in ["install_app", "install_packages"]
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


def update_environment(*dicts):
    for adict in dicts:
        env.update(adict)


def load_plugins() -> None:
    """
    Loads the available plugins located in FabSim3/plugins directory
    """

    # here, if we use the globals(), new changes will no be permanent for other
    # files, so, we need to write them into global namespace seen by this frame
    caller_globals = inspect.stack()[1][0].f_globals
    plugins = yaml.safe_load(
        open(os.path.join(env.fabsim_root, "deploy", "plugins.yml"))
    )

    for key in plugins.keys():
        plugin = {}
        plugin_dir = os.path.join(env.localroot, "plugins", key)
        if not os.path.isdir(plugin_dir):
            # if the plugin is NOT installed, do not try to load it, and go to
            # check the next plugin
            continue

        try:
            with add_print_prefix(prefix="loading plugin", color=28):
                print("{} ...".format(key))

            plugin = importlib.import_module("plugins.{}.{}".format(key, key))
            plugin_dict = plugin.__dict__

            try:
                to_import = plugin.__all__
            except AttributeError:
                to_import = [
                    name for name in plugin_dict if not name.startswith("_")
                ]

            caller_globals.update(
                {name: plugin_dict[name] for name in to_import}
            )
            env.localplugins.update({key: plugin_dir})

        except ImportError as e:
            print(e)
            raise ImportError(e)
            # pass


@beartype
def available_remote_machines() -> Dict:
    """
    This function will return the defined remote machine available in the
    machines.yml file
    """
    # find the available and defined remote machines names in machines.yml file
    # Note: default should be remove from the list
    avail_hosts = {}
    for machine_name in config.keys():
        if "remote" not in config[machine_name]:
            continue

        remote_address = config[machine_name]["remote"]
        avail_hosts.update({machine_name: remote_address})

    return avail_hosts


@task
def machine_config_info() -> None:
    """
    Print the `env` configuration variables for the input remote machine name

    Example Usage:
    ```sh
    fabsim <machine_name> print_machine_config_info
    ```
    """
    console = Console()
    console.print(
        Panel(
            pformat(config[env.host]),
            title="[green1]Defaults[/green1]",
            expand=False,
        )
    )
    console.print(
        Panel(
            pformat(user_config[env.host]),
            title="[red1]User overrides[/red1]",
            expand=False,
        )
    )


@beartype
def add_plugin_environment_variable(plugin_name: str) -> None:
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
    machine_name = env.host
    plugin_machines_user = os.path.join(
        plugin_path, "machines_{}_user.yml".format(plugin_name)
    )

    if not os.path.isfile(plugin_machines_user):
        print("\nNO machines_{}_user.yml FOUND\n".format(plugin_name))
        return

    plugin_config = yaml.load(
        open(plugin_machines_user), Loader=yaml.SafeLoader
    )

    if plugin_config is None:
        print("\nmachines_{}_user.yml is empty\n".format(plugin_name))
        return

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

    console = Console()

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

        console.print(
            Panel(
                "[red1]{}[/red1]".format(error_msg),
                title="[yellow1]Error[/yellow1]",
                expand=False,
            )
        )

    # TODO: do we need calling complete_environment() here at all ???
    complete_environment()
    msg = "\n".join(findDiff(env, old_env, path="env"))
    title = "New/Updated environment variables from {} plugin".format(
        plugin_name
    )
    console.print(
        Panel(
            "{}".format(msg),
            title="[yellow1]{}[/yellow1]".format(title),
            expand=False,
        )
    )


def my_deepcopy(obj):
    new_obj = {}
    for key in obj:
        if type(obj[key]) in [dict]:
            new_obj[key] = my_deepcopy(obj[key])
        elif isinstance(obj[key], (list)):
            new_obj[key] = obj[key][:]
        else:
            new_obj[key] = obj[key]
    return new_obj


@beartype
def findDiff(d1: Dict, d2: Dict, path: Optional[str] = "") -> List[str]:
    ret_str = []
    for key in d1:
        if key not in d2:
            ret_str.append("{} :".format(path))
            ret_str.append("  +++ {} is a new added key".format(key))
        else:
            if type(d1[key]) in [dict]:
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
