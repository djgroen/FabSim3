import subprocess
import sys


def modify_files(app):
    """
    remove @task from source files
    """
    read_the_docs_build = os.environ.get("READTHEDOCS", None) == "True"

    if read_the_docs_build:
        output_files = glob.glob("fabsim/**/*.py", recursive=True)
        print("[HAMID] {}".format(output_files))


def setup(app):

    # Add hook for building doxygen xml when needed
    app.connect("builder-inited", modify_files)
