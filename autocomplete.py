"""Helper to the FabSim3 autocomplete command."""

import os
import fnmatch

from dataclasses import dataclass, field


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


def main():
    """Main function."""

    directory_path = "plugins"
    py_files = find_py_files(directory_path)

    definitions = find_task_definitions(py_files)

    tasks = list(map(lambda x: Task(x[0], x[1]), definitions))

    for task in tasks:
        print(task)


if __name__ == "__main__":
    main()
