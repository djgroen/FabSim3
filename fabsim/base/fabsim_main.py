from __future__ import absolute_import

import builtins
import inspect
import sys
from optparse import OptionParser, make_option
from pprint import pformat, pprint

from rich import get_console
from rich import print as rich_print
from rich.panel import Panel

from fabsim.base.env import env
from fabsim.base.fab import *
from fabsim.base.utils import (
    find_all_avail_tasks,
    show_avail_machines,
    show_avail_tasks,
)
from fabsim.deploy.machines import (
    available_remote_machines,
    load_machine,
    load_plugins,
)

# from fabsim.base.decorators import add_prefix_to_print


def main():
    """
    Main FabSim3 command-line execution function
    """

    """
    # replace builtin python print function with the new print function
    # from rich module
    builtins.print = rich_print
    # use soft wrapping
    # https://github.com/willmcgugan/rich/issues/1041
    console = get_console()
    console.soft_wrap = True
    """

    # Parse command-line options
    parser = OptionParser(usage="fabsim [remote_machine] "
                          "<task>[:arg1=val1,arg2=val2,...] "
                          "[fabsim optional args]"
                          )

    optional_input_args = [
        make_option("-l", "--list",
                    action="store",
                    type='choice',
                    choices=("tasks", "machines"),
                    dest="list",
                    # default=None,
                    help="list available tasks or machines"
                    ),
    ]

    # Add in fabsim input optional arguments
    for option in optional_input_args:
        parser.add_option(option)

    options, arguments = parser.parse_args()

    #################
    # loads plugins #
    #################
    load_plugins()

    #####################################
    # find all available tasks/machines #
    #####################################
    env.avail_tasks = find_all_avail_tasks()
    env.avail_machines = available_remote_machines()

    #####################################
    # checking input optional arguments #
    #####################################
    if options.list is not None:
        if options.list.lower() == "tasks":
            # fabsim5 --list tasks
            show_avail_tasks()
            sys.exit()
        elif options.list.lower() == "machines":
            # fabsim5 --list machines
            show_avail_machines()
            sys.exit()

    ##########################################################################
    # set the target remote machine                                          #
    # by default, our assumption is the first arguments after fabsim command #
    # should be the name of target remote machine                            #
    ##########################################################################
    env.host = arguments[0]
    if env.host not in env.avail_machines:
        raise ValueError(
            "The requested remote machine \"{}\" did not listed in the "
            "machines.yml file, so it can not be used as a target remote host."
            "\n\nThe available remote machines are : \n{}".format(
                env.host, env.avail_machines.keys()
            )
        )

    ####################################################
    # check if the task is a valid FabSim3 task or not #
    ####################################################
    env.task = arguments[1].split(":", 1)[0]

    if env.task not in env.avail_tasks:
        raise RuntimeError(
            "The request task {} is not available!!".format(env.task)
        )

    env.exec_func = env.avail_tasks[env.task]

    ################################################################
    # set the task and its input args                              #
    # by default, the next input arguments after machine name is   #
    # the task name, followed by the input arguments for the task. #
    ################################################################

    # Convert key-value task args string to a dictionary
    try:
        task_args_str = arguments[1].split(":", 1)[1]
    except IndexError:
        task_args_str = None

    task_args = []
    task_kwargs = []
    if task_args_str is not None:
        for sub in task_args_str.split(","):
            if "=" in sub:
                task_kwargs.append(map(str.strip, sub.split("=", 1)))
            else:
                task_args.append(sub)

    env.task_args = task_args
    env.task_kwargs = dict(task_kwargs)

    ############################################
    # Load the machine-specific configurations #
    ############################################
    load_machine(env.host)

    ##############################
    # execute the requested task #
    ##############################
    env.exec_func(*env.task_args, **env.task_kwargs)


if __name__ == '__main__':
    main()
