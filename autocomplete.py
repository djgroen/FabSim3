import os
import fnmatch
import re
import json
from typing import List, Tuple, Dict

import yaml

def main():
    # Set the directory path to search for Python files
    directory_path = "plugins"
    # Find Python files in the specified directory using list comprehension
    py_files = [os.path.join(root, filename) for root, _, files in os.walk(directory_path) for filename in fnmatch.filter(files, "*.py")]

    # Find task definitions in the Python files and extract their details
    definitions = []
    track = False
    start = False
    deflines = []

    for file in py_files:
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

    # Get a list of machine names from the YAML file
    with open("fabsim/deploy/machines.yml", "r", encoding="utf-8") as file_handler:
        machines = yaml.safe_load(file_handler)

    machines_list = list(machines.keys())

    # Concatenate machine names into a single string without ", " pattern
    machines_str = " ".join(machines_list)

    # Create a dictionary to store the autocompletion options for Bash
    lists_dict = {"machines": machines_str}

    # Populate the dictionary with task names and their arguments using list comprehension
    for file, definition in definitions:
        if not definition.startswith("def"):
            raise ValueError("Task definition must start with 'def'.")

        name = definition.split(" ")[1].split("(")[0]
        all_arguments = definition.split("(")[1].split(")")[0].split(",")

        # Create a list to store all arguments (including optional arguments) using list comprehension
        arguments_list = [arg.split("=")[0].strip() if "=" in arg else arg.strip() for arg in all_arguments]

        arguments = " ".join(arguments_list)
        arguments = "".join(arguments.split("**")).replace("args", "")
        arguments = re.sub(r"\s+", " ", arguments).strip()

        key = name
        value = arguments
        lists_dict.setdefault(key, []).append(value)

    # Print the JSON format for Bash processing
    print(json.dumps(lists_dict))

if __name__ == "__main__":
    main()
