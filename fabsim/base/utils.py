import inspect
import os
import platform
import subprocess
import sys
import time
from contextlib import contextmanager
from os import system
from pathlib import Path
from pprint import pprint
from tempfile import NamedTemporaryFile

from beartype.typing import Dict
from rich import print as rich_print
from rich.console import Console
from rich.panel import Panel
from rich.table import Table, box
from rich.text import Text

from fabsim.base.env import env


def find_all_avail_tasks() -> Dict:
    """
    Finds and returns the list of callable tasks.
    Within FabSim3, each function that wrapped by @task can be called from
    command line.
    Returns:
        array of function object
    """
    f_globals = inspect.stack()[1][0].f_globals
    avail_tasks = {
        k: v
        for k, v in f_globals.items()
        if callable(v) and hasattr(v, "__wrapped__")
    }

    return avail_tasks


def show_avail_machines() -> None:
    """
    Print the available remote machines for job submission
    """
    avail_machines_list = env.avail_machines
    table = Table(
        title="\n\nList of available remote machines",
        show_header=True,
        box=box.ROUNDED,
        header_style="dark_cyan",
    )
    table.add_column("remote machine name", style="blue")
    table.add_column("remote machine address", style="magenta")

    for machine_name, machine_address in env.avail_machines.items():
        table.add_row(machine_name, machine_address)
    console = Console()
    console.print(table)


def show_avail_tasks() -> None:
    """
    Print the available and callable tasks (FabSim3 APIs or plugins tasks)
    """
    avail_task_dict = {}
    for task_name, task_obj in env.avail_tasks.items():
        if not hasattr(task_obj, "task_type"):
            continue

        if hasattr(task_obj, "plugin_name"):
            key = "{} {}".format(task_obj.plugin_name, task_obj.task_type)
        else:
            key = "{}".format(task_obj.task_type)

        if key not in avail_task_dict:
            avail_task_dict.update({key: []})
        avail_task_dict[key].append(task_name)

    table = Table(
        title="\n\nList of available Tasks",
        show_header=True,
        show_lines=True,
        # expand=True,
        box=box.ROUNDED,
        header_style="dark_cyan",
    )
    table.add_column("Task Type", style="blue")
    table.add_column("Tasks name", style="magenta")

    for task_type, tasks_name in avail_task_dict.items():
        table.add_row(
            "{}".format(task_type),
            "{}".format(", ".join(tasks_name)),
        )
    console = Console()
    console.print(table)


class Prefixer(object):
    def __init__(self, prefix, orig):
        self.prefix = prefix
        self.orig = orig

    def write(self, text):
        for t in text.rstrip().splitlines():
            self.orig.write(self.prefix + t + "\n")

    def __getattr__(self, attr):
        return getattr(self.orig, attr)


def colored(color_code, text):
    return "\033[38;5;{}m{}\033[0;0m ".format(color_code, text)


@contextmanager
def add_print_prefix(prefix, color=24):
    # source : https://stackabuse.com/how-to-print-colored-text-in-python

    current_out = sys.stdout
    try:
        sys.stdout = Prefixer(
            prefix=colored(color, "[{}]".format(prefix)), orig=current_out
        )
        yield
    finally:
        sys.stdout = current_out


class OpenVPNContext(object):
    """
    Connect to and disconnect from OpenVPN,
    if a configuration is specified in the environment.
    Otherwise, do nothing.

    Usage:
    ```python
    with OpenVPNContext(env):
        # do stuff while (potentially) connected through VPN
    ```
    """

    _AUTH_ENV_VARS = ['OPENVPN_AUTH_USER', 'OPENVPN_AUTH_PASS']

    def __init__(self, env):
        self._config = None
        self._auth_user_pass = None
        path_err_msg = 'The value of X for this machine is not a valid file.'
        if hasattr(env, "openvpn_config"):
            self._config = env.openvpn_config
            if not Path(self._config).is_file():
                print(path_err_msg.replace('X', self._config), file=sys.stderr)
                exit(1)
        env_key_auth = 'openvpn_auth_user_pass'
        if hasattr(env, env_key_auth):
            self._auth_user_pass = env[env_key_auth]
            if not isinstance(self._auth_user_pass, bool) or \
                (isinstance(self._auth_user_pass, str) and
                    not Path(self._auth_user_pass).is_file()):
                print(path_err_msg.replace(
                    'X', self._auth_user_pass)[:-1] + ' or boolean.',
                    file=sys.stderr)
                exit(1)
            if len(set(OpenVPNContext._AUTH_ENV_VARS)
                   .intersection(os.environ)) != 2:
                print(' and '.join(OpenVPNContext._AUTH_ENV_VARS) +
                      f' must be set in environment if {env_key_auth} is true.')
                exit(1)

    def _print(msg):
        rich_print(
            Panel.fit(
                msg,
                title=f"[yellow]{OpenVPNContext.__name__}[/yellow]",
                border_style="yellow",
            )
        )

    def __enter__(self):
        self._p = None
        if self._config is not None:
            OpenVPNContext._print("Starting VPN...")
            cmd = ["openvpn", "--config", self._config]
            if platform.system().lower() in ["linux", "darwin"]:
                cmd = ["sudo", "-n"] + cmd  # OpenVPN requires root privileges
            # Create a temporary file for holding credentials from environment
            # (Workaround: The shell might not support the <() operator and
            #  using pipes does not seem to work with the OpenVPN client)
            with NamedTemporaryFile(mode='wt', delete=True) as temporaryFile:
                if self._auth_user_pass is True:
                    for v in OpenVPNContext._AUTH_ENV_VARS:
                        temporaryFile.write(f'{os.environ[v]}\n')
                    temporaryFile.flush()
                    self._auth_user_pass = temporaryFile.name
                if type(self._auth_user_pass) is str:
                    cmd += ["--auth-user-pass", self._auth_user_pass]
                self._p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL)
                # Wait a bit for the VPN connection to be established
                time.sleep(3)
            if platform.system().lower() in ["linux", "darwin"]:
                system("stty sane")  # sudo messes up the terminal output
            if self._p.poll() is not None:
                OpenVPNContext._print("VPN not running")
                exit(1)

    def __exit__(self, exc_type, exc_value, traceback):
        if self._p is not None:
            OpenVPNContext._print("Stopping VPN...")
            try:
                self._p.kill()
                self._p = None
            except Exception as e:
                pass
