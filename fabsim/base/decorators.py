import os
import inspect
from functools import wraps
from beartype import beartype
from fabsim.base.env import env
from fabsim.base.utils import add_print_perfix, colored

from pprint import pprint


"""
def colored(r, g, b, text):
    return "\033[38;2;{};{};{}m{}\033[38;2;255;255;255m".format(r, g, b, text)


def add_prefix_to_print(prefix=""):

    # Add a prefix to print function

    # Name            │ Hex     │ RGB
    # orange_red1     │ #ff5f00 │ rgb(255,95,0)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            pprint("calling add_prefix_to_print")
            if len(prefix) > 0:
                return func(
                    colored(255, 95, 0, "[{}]".format(prefix)),
                    *args, **kwargs)
            else:
                return func(*args, **kwargs)

        return wrapper

    return decorator


def add_prefix_decorator_to_print(prefix):

    # Add a prefix to print function

    # Name            │ Hex     │ RGB
    # orange_red1     │ #ff5f00 │ rgb(255,95,0)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            pprint("calling add_prefix_decorator_to_print")
            return func(
                colored(255, 95, 0, "[{}]".format(prefix)),
                *args, **kwargs)

        return wrapper

    return decorator
"""


def task(func):
    """
    FabSim decorator for make the py function callable from command-line.
    the attribute has_been_called will be used if we detect a function has been
    wrapped or not :) It can also be used to check if the wrapped function is
    already called or not
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        wrapper.has_been_called = True
        with add_print_perfix(prefix="Executing task", color=196):
            print("{}".format(func.__name__))

        return func(*args, **kwargs)

    wrapper.has_been_called = False
    func_dir = os.path.dirname(os.path.abspath(inspect.getfile(func)))
    # find the type of task, is FabSim3 API or plugin task
    if env.plugins_root in func_dir:
        wrapper.task_type = "Plugin"
        wrapper.plugin_name = os.path.basename(func_dir)
    elif env.fabsim_root in func_dir:
        wrapper.task_type = "FabSim3_API"
    else:
        wrapper.task_type = "NOT KNOWN"

    return wrapper


@beartype
def load_plugin_env_vars(plugin_name: str):
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
    from fabsim.deploy.machines import add_plugin_environment_variable

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
