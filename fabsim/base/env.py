"""Environment variable for FabSim3."""
# pylint: disable=invalid-name
# pylint: disable=import-outside-toplevel

import getpass
import io
import os
import posixpath

from rich.console import Console
from rich.table import Table, box

# Better Logging and Tracebacks with Rich :)
# traceback.install()
# any data structures will be pretty printed and highlighted
# pretty.install()


# inspired by fabric 1.x
# https://github.com/fabric/fabric/blob/1.10/fabric/utils.py#L186
class _lookupDict(dict):
    """
    Dictionary superclass which allows users to have direct access to
    key/values.
    t=_lookupDict({"x" : 56})
    t.x is equivalent to t["x"]
    """

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            # to conform with __getattr__ spec
            raise AttributeError(key)  # pylint: disable=raise-missing-from

    def __setattr__(self, key, value):
        self[key] = value

    def __str__(self):
        if not env.rich_console:
            from pprint import pformat

            return pformat(self)
        table = Table(
            title="\n\nFabSim3 Environment variables",
            show_header=True,
            show_lines=True,
            expand=True,
            box=box.ROUNDED,
            header_style="dark_cyan",
        )
        table.add_column("Variables", style="blue")
        table.add_column("Value", style="magenta")
        for key, value in self.items():
            table.add_row(key, f"{value}")
        # console = Console()
        # console.print(table)
        f = io.StringIO()
        console = Console(file=f, force_terminal=True)
        console.print(table)
        return f.getvalue()


work_dir = os.path.dirname(os.path.abspath(__file__))
localroot = os.path.dirname(os.path.dirname(work_dir))
fabsim_root = os.path.dirname(work_dir)
plugins_root = os.path.join(localroot, "plugins")
ssh_default_port = "22"
env = _lookupDict(
    {
        "host": None,
        "username": None,
        "default_port": ssh_default_port,
        "port": ssh_default_port,
        "avail_hosts": [],
        "local_user": getpass.getuser(),
        "use_sudo": False,
        "task": None,
        "task_args": [],
        "task_kwargs": {},
        "localroot": localroot,
        "fabsim_root": fabsim_root,
        "plugins_root": plugins_root,
        "localplugins": {},
        "acceptable_err_subprocesse_ret_codes": [0],
        "command_prefixes": [],
        "pather": posixpath,
        "replicas": 1,
        "max_job_name_chars": 15,
        "local_templates_path": [
            os.path.join(fabsim_root, "deploy", "templates")
        ],
        "local_config_file_path": [os.path.join(fabsim_root, "config_files")],
        "default_ssh_config_path": os.path.join(
            os.path.expanduser("~"), ".ssh", "config"
        ),
    }
)
