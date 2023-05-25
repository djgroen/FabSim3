import inspect
import sys
from contextlib import contextmanager
from pprint import pprint

from beartype.typing import Dict
from rich.console import Console
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
def add_print_perfix(prefix, color=24):
    # source : https://stackabuse.com/how-to-print-colored-text-in-python

    current_out = sys.stdout
    try:
        sys.stdout = Prefixer(
            prefix=colored(color, "[{}]".format(prefix)), orig=current_out
        )
        yield
    finally:
        sys.stdout = current_out
