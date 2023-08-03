import os
import fnmatch
import re
import json
from typing import List, Tuple, Dict

import yaml

def main():
    
    # Check if the FABSIM3_PATH environment variable is set
    if "FABSIM3_HOME" not in os.environ:
        print("Error: FABSIM3_HOME environment variable is not set!")
        exit(1)

    # Get the FABSIM3_HOME path from the environment variable
    fabsim3_home = os.environ["FABSIM3_HOME"]
    
    # Set the directory path to search for Python files (using FABSIM3_HOME)
    directory_path = os.path.join(fabsim3_home, "plugins")
    
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
                        
        
    # Get the path to the machines.yml file using FABSIM3_HOME
    machines_file_path = os.path.join(fabsim3_home, "fabsim", "deploy", "machines.yml")

    # Check if the machines.yml file exists
    if not os.path.isfile(machines_file_path):
        print(f"Error: machines.yml file not found in {machines_file_path}")
        exit(1)

    # Load the machines.yml file
    with open(machines_file_path, "r", encoding="utf-8") as file_handler:
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
