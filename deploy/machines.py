# -*- coding: utf-8 -*-
#
# This source file is part of the FabSim software toolkit, which is distributed
# under the BSD 3-Clause license.
# Please refer to LICENSE for detailed information regarding the licensing.
#
# This file contains functions which help parse and process
# machine-specific definitions, written in machines*.yml

"""
Module defining how we configure the fabric environment for target machines.
Environment is loaded from YAML dictionaries machines.yml and machines_user.yml
"""
# If we're running in an activated virtualenv, use that.
import site
import os
from sys import version_info
import sys
import fabric.api
from fabric.api import env, task, execute, cd, prefix
import sys
import posixpath
import yaml
from .templates import *
from functools import *
from pprint import PrettyPrinter
pp = PrettyPrinter()

if 'VIRTUAL_ENV' in os.environ:
    virtual_env = os.path.join(os.environ.get('VIRTUAL_ENV'),
                               'lib',
                               'python%d.%d' % version_info[:2],
                               'site-packages')
    site.addsitedir(virtual_env)
    print('Using Virtualenv =>', virtual_env)
del site, version_info

# Root of local FabSim installation
env.localroot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env.localhome = os.path.expanduser("~")
env.localplugins = {}  # dict containing local paths to all plugins.
env.no_ssh = False
env.no_hg = False
# Load and invoke the default non-machine specific config JSON dictionaries.
config = yaml.load(open(os.path.join(env.localroot, 'deploy',
                                     'machines.yml')), Loader=yaml.SafeLoader)
env.update(config['default'])
user_config = yaml.load(open(os.path.join(
    env.localroot, 'deploy', 'machines_user.yml')), Loader=yaml.SafeLoader)
env.update(user_config['default'])
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

env.pythonroot = os.path.join(env.localroot, 'python')
env.blackboxroot = os.path.join(env.localroot, 'blackbox')

# job database configuration for remote machines
# env.local_jobsDB_path = path.join(env.localroot, 'deploy', '.jobsDB')
# env.local_jobsDB_filename = 'jobsDB.txt'
env.replicas = 1


def generate_module_commands(script=None):
    # Not using get as I want this to crash if the all key does not exist (it
    # should always be present).
    module_commands = ["module %s" % module
                       for module in env.modules["all"]]

    module_commands += ["module %s" % module
                        for module in env.modules.get("nonexistent", "")]

    module_commands += ["module unload %s" % module
                        for module in env.modules.get("unloaded", "")]
    module_commands += ["module load %s" % module
                        for module in env.modules.get("loaded", "")]
    if script is not None:
        # Not using get as I want this to crash if the all key does not exist
        # (it should always be present).
        module_commands += ["module %s" % module
                            for module in env.modules.get(script, "")]
    # print("MODULE COMMANDS: ", module_commands)
    return module_commands


module_commands = generate_module_commands()
env.run_prefix = " \n".join(module_commands +
                            list(map(template, run_prefix_commands))) \
    or 'echo THE FIRST Running...'

if (not any("install_app" in str or "install_packages" in str
            for str in env.tasks) and
        hasattr(env, 'venv') and
        str(env.venv).lower() == 'true'):
    # since we are going to load python VirtualEnv, so, it would be better
    # to unload any current loaded python modules, in order to avoid
    # conflicts during the execution of python program
    env.run_prefix = env.run_prefix +\
        "\n# load python from VirtualEnv" +\
        "\nmodule unload python\n" +\
        "source %s/bin/activate" % (env.virtual_env_path)


@task
def machine(name):
    """
    Load the machine-specific configurations.
    Completes additional paths and interpolates them, via complete_environment.
    Usage, e.g. fab machine:hector build
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
def print_machine_config_info(name=""):
    if name == "":
        print("Usage: \
            fabsim localhost print_machine_config_info:<machine_name>")
        sys.exit()
    print_msg_box("Defaults: ")
    pp.pprint(config[name])
    print_msg_box("User overrides: ", )
    pp.pprint(user_config[name])
    '''
    for plugin_name in plugins_config:
        try:
            print_msg_box("%s plugin overrides: " % (plugin_name))
            pp.pprint(plugins_config[plugin_name][name])
        except KeyError:
            pass
    '''
# Metaprogram the machine wrappers
for machine_name in set(config.keys()) - set(['default']):
    globals()[machine_name] = task(alias=machine_name)(
        partial(machine, machine_name))


def load_plugin_env_vars(plugin_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print("calling task %s from plugin %s" %
                  (func.__name__, plugin_name))
            add_plugin_environment_variable(plugin_name)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def add_plugin_environment_variable(plugin_name):
    # machines_<plugin>.yml
    # machines_<plugin>_user.yml
    plugin_path = os.path.join(env.localroot, "plugins", plugin_name)
    machine_name = env.machine_name
    plugin_machines_user = os.path.join(plugin_path,
                                        "machines_%s_user.yml" % (plugin_name)
                                        )

    if not os.path.isfile(plugin_machines_user):
        return

    plugin_config = yaml.load(open(plugin_machines_user),
                              Loader=yaml.SafeLoader
                              )

    # only update environment variable based on plugin_machines_user yaml file
    old_env = my_deepcopy(env)
    if "import" in config[machine_name]:
        if config[machine_name]["import"] in plugin_config:
            env.update(plugin_config[config[machine_name]["import"]])

    if "default" in plugin_config and\
            plugin_config['default'] is not None:
        env.update(plugin_config['default'])

    if machine_name in plugin_config and\
            plugin_config[machine_name] is not None:
        env.update(plugin_config[machine_name])

    env.modules = config["default"]["modules"]
    if "import" in config[machine_name]:
        if config[machine_name]["import"] in plugin_config:
            env.modules.update(
                plugin_config[config[machine_name]["import"]].modules)

    if machine_name in plugin_config and\
            plugin_config[machine_name] is not None:
        env.modules.update(plugin_config[machine_name].get("modules", {}))
    else:
        error_msg = "%s is not available in %s" % (
            machine_name, plugin_machines_user)
        error_msg += "\nor there is no item for that machine name"
        print_msg_box(error_msg)

    complete_environment()
    print_msg_box("\n".join(findDiff(env, old_env, path="env")),
                  title="New/Updated environment variables from %s plugin"
                  % (plugin_name))


def complete_environment():
    """Add paths to the environment based on information in the JSON configs.
    Templates are filled in from the dictionary to allow $foo interpolation
    in the JSON file.
    Environment vars created can be used in job-script templates:
    results_path: Path to store results
    remote_path: Root of area for checkout and build on remote
    config_path: Path to store config files
    repository_path: Path of remote mercurial checkout
    tools_path: Path of remote python 'Tools' folder
    tools_build_path: Path of disttools python 'build' folder for python tools
    regression_test_path: Path on remote to diffTest
    build_path: Path on remote to HemeLB cmake build area.
    scripts_path: Path where job-queue-submission scripts generated
    by Fabric are sent.
    cmake_flags: Flags to pass to cmake
    run_prefix: Command string to invoke before any job is run.
    build_prefix: Command string to invoke before builds/installs are attempted
    build_number: Tip revision number of mercurial repository.
    """
    env.hosts = ['%s@%s' % (env.username, env.remote)]
    env.host_string = '%s@%s' % (env.username, env.remote)
    env.home_path = template(env.home_path_template)
    env.runtime_path = template(env.runtime_path_template)
    env.work_path = template(env.work_path_template)
    env.remote_path = template(env.remote_path_template)
    env.stat = template(env.stat)
    env.results_path = env.pather.join(env.work_path, "results")
    env.config_path = env.pather.join(env.work_path, "config_files")
    env.scripts_path = env.pather.join(env.work_path, "scripts")
    env.local_results = os.path.expanduser(template(env.local_results))

    if hasattr(env, 'flee_location'):
        env.flee_location = template(env.flee_location)

    for i in range(0, len(env.local_templates_path)):
        env.local_templates_path[i] = os.path.expanduser(
            template(env.local_templates_path[i]))

    for i in range(0, len(env.local_config_file_path)):
        env.local_config_file_path[i] = os.path.expanduser(
            template(env.local_config_file_path[i]))

    # module_commands = generate_module_commands()
    module_commands = generate_module_commands(script=env.get("script", None))
    run_prefix_commands = env.run_prefix_commands[:]
    env.run_prefix = " \n".join(
        module_commands +
        list(map(template, map(template, run_prefix_commands)))) \
        or '/bin/true || true'
    # This echo is commented because can cause problem for slurmID saving
    # or 'echo The Running...'

    if env.temp_path_template:
        env.temp_path = template(env.temp_path_template)

    if (hasattr(env, 'virtual_env_path') and env.virtual_env_path):
        env.virtual_env_path = template(env.virtual_env_path)

    if (hasattr(env, 'app_repository') and env.app_repository):
        env.app_repository = template(env.app_repository)

    if (not any("install_app" in str or "install_packages" in str
                for str in env.tasks) and
            hasattr(env, 'venv') and
            str(env.venv).lower() == 'true'):
        # since we are going to load python VirtualEnv, so, it would be better
        # to unload any current loaded python modules, in order to avoid
        # conflicts during the execution of python program
        env.run_prefix = env.run_prefix +\
            "\n# load python from VirtualEnv" +\
            "\nmodule unload python\n" +\
            "source %s/bin/activate" % (env.virtual_env_path)
    # env.build_number=subprocess.check_output(['hg','id','-q'.'-i']).strip()
    # check_output is 2.7 python and later only. Revert to oldfashioned popen.
    # cmd=os.popen(template("hg id -q -i"))
    # cmd.close()
    # env.build_number=run("hg id -q -i")

# complete_environment()


def my_deepcopy(obj):
    new_obj = {}
    for key in obj:
        if type(obj[key]) in [dict, fabric.utils._AliasDict]:
            new_obj[key] = my_deepcopy(obj[key])
        elif isinstance(obj[key], (list)):
            new_obj[key] = obj[key][:]
        else:
            new_obj[key] = obj[key]
    return new_obj


def findDiff(d1, d2, path=""):
    ret_str = []
    for key in d1:
        if (key not in d2):
            ret_str.append("%s :" % (path))
            ret_str.append("  +++ %s is a new added key" % (key))
        else:
            if type(d1[key]) in [dict, fabric.utils._AliasDict]:
                if path == "":
                    nested_path = key
                else:
                    nested_path = path + "->" + key
                ret_str += findDiff(d1[key], d2[key], nested_path)
            elif isinstance(d1[key], (bool, str, int)):
                if d1[key] != d2[key]:
                    ret_str.append("%s :" % (path))
                    ret_str.append("  --- %s : %s" % (key, str(d2[key])))
                    ret_str.append("  +++ %s : %s" % (key, str(d1[key])))
                else:
                    pass
            elif isinstance(d1[key], (list)):
                if set(d1[key]) != set(d2[key]):
                    ret_str.append("%s :" % (path))
                    ret_str.append("  --- %s : %s" % (key, str(d2[key])))
                    ret_str.append("  +++ %s : %s" % (key, str(d1[key])))

    return ret_str


def print_msg_box(msg, indent=1, width=None, title=None, border="═"):
    """
        Print message-box with optional title.
        source : https://stackoverflow.com/questions/39969064/how-to-print-a-message-box-in-python
    """
    if len(msg) == 0:
        return

    if border == "═":
        t_l = "╔"
        t_r = "╗"
        b_l = "╚"
        b_r = "╝"
        l = r = "║"
        t = b = "═"
    elif border == "-":
        t_l = "┌"
        t_r = "┐"
        b_l = "└"
        b_r = "┘"
        l = r = "|"
        t = b = "─"
    lines = msg.split('\n')

    space = " " * indent
    if not width:
        width = max(map(len, lines))
    box = f'{t_l}{t * (width + indent * 2)}{t_r}\n'  # upper_border
    if title:
        box += f'{l}{space}{title:<{width}}{space}{r}\n'  # title
        # underscore
        box += f'{l}{space}{"-" * len(title):<{width}}{space}{r}\n'
    box += ''.join([f'{l}{space}{line:<{width}}{space}{r}\n' for line in lines])
    box += f'{b_l}{b * (width + indent * 2)}{b_r}'  # lower_border
    print(box)
