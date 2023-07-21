"""Helper to the FabSim3 autocomplete command."""

import os
import fnmatch
import re

from dataclasses import dataclass, field

import yaml


def get_machines(filemane):
    """Get the machines from the machines.yml file."""

    with open(filemane, "r", encoding="utf-8") as file_handler:
        machines = yaml.safe_load(file_handler)

    return list(machines.keys())


def remove_consecutive_spaces(input_string):
    """Remove consecutive spaces from a string."""

    return re.sub(r"\s+", " ", input_string)


@dataclass
class Task:
    """A FabSim3 task."""

    plugin: str
    definition: str = field(repr=False)
    name: str = field(init=False)
    arguments: list[str] = field(default_factory=list)
    optional_arguments: list[str] = field(default_factory=list)
    optional_arguments_default: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.definition.startswith("def"):
            raise ValueError("Task definition must start with 'def'.")

        self.name = self.definition.split(" ")[1].split("(")[0]

        all_arguments = self.definition.split("(")[1].split(")")[0].split(",")

        for argument in all_arguments:
            if "=" in argument:
                self.optional_arguments.append(argument.split("=")[0].strip())
                self.optional_arguments_default.append(
                    argument.split("=")[1].strip()
                )
            else:
                self.arguments.append(argument)


def find_py_files(directory: str) -> list[str]:
    """Find all python files in a directory."""

    py_files = []
    for root, _, files in os.walk(directory):
        for filename in fnmatch.filter(files, "*.py"):
            py_files.append(os.path.join(root, filename))
    return py_files


def find_task_definitions(files: list[str]) -> list[tuple[str, str]]:
    """Find all FabSim3 tasks in a directory."""

    definitions = []
    track = False
    start = False
    deflines = []

    for file in files:
        # Open the file
        with open(file, "r", encoding="utf-8") as file_handler:
            lines = file_handler.readlines()

        # Find the tasks
        for line in lines:
            if "#" in line:
                line = line.split("#")[0]

            if "@task" in line:
                track = True
                continue
            if track:
                if "def" in line:
                    start = True

                if start:
                    deflines.append(line.strip())
                    if line.strip().endswith(":"):
                        track = False
                        start = False
                        definitions.append(
                            (file.split("/")[-1], "".join(deflines).strip())
                        )
                        deflines = []

    return definitions


def write_to_file_task_args(
    tasks: list[Task], filename: str, standalone_file: str, with_args_file: str
):
    """Write the task arguments to a file."""

    standalone = []
    with_args = []

    with open(filename, "w", encoding="utf-8") as file_handler:
        for task in tasks:
            string1 = " ".join(task.arguments)
            string2 = " ".join(task.optional_arguments)
            string = string1 + " " + string2

            string = string.replace("**", "")
            string = string.replace("args", "")

            string = remove_consecutive_spaces(string)

            string = string.strip()

            if len(string) == 0:
                standalone.append(task.name)
            else:
                with_args.append(task.name)
                file_handler.write(f'{task.name}="')
                file_handler.write(f'{string}"\n')

    with open(standalone_file, "w", encoding="utf-8") as file_handler:
        file_handler.write('standalone_tasks="')
        file_handler.write(" ".join(standalone))
        file_handler.write('"\n')

    with open(with_args_file, "w", encoding="utf-8") as file_handler:
        file_handler.write('tasks_with_args="')
        file_handler.write(" ".join(with_args))
        file_handler.write('"\n')


def write_machines_to_file(machines: list[str], filename: str):
    """Write the machines to a file."""

    with open(filename, "w", encoding="utf-8") as file_handler:
        file_handler.write('machines="')
        file_handler.write(" ".join(machines))
        file_handler.write('"\n')


def main():
    """Main function."""

    directory_path = "plugins"
    py_files = find_py_files(directory_path)

    definitions = find_task_definitions(py_files)

    tasks = list(map(lambda x: Task(x[0], x[1]), definitions))
    machines = get_machines("fabsim/deploy/machines.yml")

    write_to_file_task_args(
        tasks, "task_args.txt", "standalone_tasks.txt", "tasks_with_args.txt"
    )
    write_machines_to_file(machines, "machines.txt")


if __name__ == "__main__":
    main()
