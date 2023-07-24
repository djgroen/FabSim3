"""
This script:
Searches python scripts in designated directories,
Creates dictionary for fabsim autocompete in bash,
Stores dict in JSON format.
"""

import os
import fnmatch
import re
import json

from typing import List, Tuple, Dict

import yaml

def get_machines(filename: str) -> List[str]:
    with open(filename, "r", encoding="utf-8") as file_handler:
        machines = yaml.safe_load(file_handler)

    return list(machines.keys())

class Task:
    def __init__(self, plugin: str, definition: str):
        self.plugin = plugin
        self.definition = definition
        self.name = ""
        self.arguments = []
        self.optional_arguments = []
        self.optional_arguments_default = []
        self.__post_init()

    def __post_init(self):
        if not self.definition.startswith("def"):
            raise ValueError("Task definition must start with 'def'.")

        self.name = self.definition.split(" ")[1].split("(")[0]

        all_arguments = self.definition.split("(")[1].split(")")[0].split(",")

        for argument in all_arguments:
            if "=" in argument:
                self.optional_arguments.append(argument.split("=")[0].strip())
                self.optional_arguments_default.append(argument.split("=")[1].strip())
            else:
                self.arguments.append(argument)

def find_py_files(directory: str) -> List[str]:
    py_files = []
    for root, _, files in os.walk(directory):
        for filename in fnmatch.filter(files, "*.py"):
            py_files.append(os.path.join(root, filename))
    return py_files


def find_task_definitions(files: List[str]) -> List[Tuple[str, str]]:
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
                        definitions.append((file.split("/")[-1], "".join(deflines).strip()))
                        deflines = []

    return definitions


def main():
    # Set the directory path to search for Python files
    directory_path = "plugins"
    # Find Python files in the specified directory
    py_files = find_py_files(directory_path)

    # Find task definitions in the Python files and extract their details
    definitions = find_task_definitions(py_files)

    # Create Task objects from the extracted definitions
    tasks = list(map(lambda x: Task(x[0], x[1]), definitions))
    
    # Get a list of machine names from the YAML file
    machines_list = get_machines("fabsim/deploy/machines.yml")

    # Concatenate machine names into a single string without ", " pattern
    machines = " ".join(machines_list)
    
    # Create a dictionary to store the autocompletion options for Bash
    lists_dict = {}
    # Add the machine names to the dictionary
    lists_dict["machines"] = machines
    
    # Populate the dictionary with task names and their arguments
    for task in tasks:
        print(task.name)
        arguments = " ".join(task.arguments)
        optional_arguments = " ".join(task.optional_arguments)
        combined = arguments + " " + optional_arguments
        combined = combined.replace("**", "")
        combined = combined.replace("args", "")
        combined = re.sub(r"\s+", " ", combined)
        combined = combined.strip()
        key = task.name
        value = combined
        if key in lists_dict:
            lists_dict[key].append(value)
        else:
            lists_dict[key] = [value]
            
    # Print the JSON format for Bash processing
    print(json.dumps(lists_dict))

if __name__ == "__main__":
    main()
