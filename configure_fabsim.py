import os
import sys
import subprocess
import platform
import getpass
from shutil import which

from pprint import pprint
import importlib


def install_required_modules(pkg_name: str, pip_pkg_name: str = None) -> bool:
    """
    Import a Module,
    if that fails, try to use the command pip to install it.
    """
    already_installed = False
    if pip_pkg_name is None:
        pip_pkg_name = pkg_name
    try:
        # If Module it is already installed, try to Import it
        importlib.import_module(pkg_name)
        already_installed = True
    except ImportError:
        # Error if Module is not installed Yet, then install it

        check_call_list = ["python3", "-m", "pip", "install", pip_pkg_name]
        if pip_pkg_name == "fabric2":
            check_call_list.append("invoke==2.2.0")

        print("Installing {} package ...".format(pkg_name))
        if bool(os.environ.get("VIRTUAL_ENV")) is True:
            print("Executing : python3 -m pip install {}".format(pip_pkg_name))

            subprocess.check_call(check_call_list)

        else:
            print(
                "Executing : python3 -m pip install --user {}".format(
                    pip_pkg_name
                )
            )
            subprocess.check_call(check_call_list)

    return already_installed


# rich emojis list
# https://github.com/willmcgugan/rich/blob/master/rich/_emoji_codes.py
# rich colors list
# https://github.com/willmcgugan/rich/blob/master/docs/source/appendix/colors.rst
console = None
yaml = None

required = {
    "rich": None,
    "ruamel.yaml": None,
    "numpy": None,
    "yaml": "pyyaml",
    "fabric2": "fabric2",
    "beartype": "beartype",
}

for pkg_name, pip_pkg_name in required.items():
    already_installed = install_required_modules(pkg_name, pip_pkg_name)
    if pkg_name == "rich":
        from rich.console import Console
        from rich import print
        from rich.panel import Panel
        from rich.syntax import Syntax

        console = Console()

    if pkg_name == "ruamel.yaml":
        import ruamel.yaml

        yaml = ruamel.yaml.YAML()

    if already_installed:
        console.print(
            "Package {} is already installed :thumbs_up:".format(pkg_name),
            style="green",
        )
    else:
        console.print(
            "Package {} is installed in your system :party_popper:".format(
                pkg_name
            ),
            style="yellow",
        )


yaml.allow_duplicate_keys = None
yaml.preserve_quotes = True
# to Prevent long lines getting wrapped in ruamel.yaml
yaml.width = 4096  # or some other big enough value to prevent line-wrap


def get_platform():
    platforms = {
        "linux": "Linux",
        "linux1": "Linux",
        "linux2": "Linux",
        "linux3": "Linux",
        "darwin": "OSX",
        "win32": "Windows",
    }
    try:
        return platforms[sys.platform]
    except Exception:
        print("[{}] Unidentified system !!!".format(sys.platform))
        exit()


class AttributeDict(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            # to conform with __getattr__ spec
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        del self[key]


def linux_distribution():
    try:
        return platform.linux_distribution()
    except Exception:
        return "N/A"


FS3_env = AttributeDict(
    {
        "OS_system": get_platform(),
        "OS_release": platform.release(),
        "OS_version": platform.version(),
        # os.getcwd() : not working if your call is outside of FabSim3 folder
        "FabSim3_PATH": os.path.dirname(os.path.realpath(__file__)),
        "user_name": getpass.getuser(),
        "machines_user_yml": None,
    }
)


def config_yml_files():
    # Load and invoke the default non-machine specific config JSON
    # dictionaries.
    FS3_env.machines_user_yml = yaml.load(
        open(
            os.path.join(
                FS3_env.FabSim3_PATH,
                "fabsim",
                "deploy",
                "machines_user_example.yml",
            )
        )
    )
    # setup machines_user.yml
    S = ruamel.yaml.scalarstring.DoubleQuotedScalarString
    FS3_env.machines_user_yml["localhost"]["home_path_template"] = S(
        os.path.join(FS3_env.FabSim3_PATH, "localhost_exe")
    )
    FS3_env.machines_user_yml["default"]["home_path_template"] = S(
        os.path.join(FS3_env.FabSim3_PATH, "localhost_exe")
    )
    FS3_env.machines_user_yml["default"]["local_results"] = os.path.join(
        FS3_env.FabSim3_PATH, "results"
    )
    FS3_env.machines_user_yml["default"]["local_configs"] = os.path.join(
        FS3_env.FabSim3_PATH, "config_files"
    )
    FS3_env.machines_user_yml["default"]["username"] = FS3_env.user_name
    FS3_env.machines_user_yml["localhost"]["username"] = FS3_env.user_name

    machines_user_PATH = os.path.join(
        FS3_env.FabSim3_PATH, "fabsim", "deploy", "machines_user.yml"
    )

    # backup the machines_user.yml if it exits
    if os.path.isfile(machines_user_PATH):
        os.rename(
            machines_user_PATH,
            os.path.join(
                FS3_env.FabSim3_PATH,
                "fabsim",
                "deploy",
                "machines_user_backup.yml",
            ),
        )

    # save machines_user.yml
    with open(machines_user_PATH, "w") as yaml_file:
        yaml.dump(FS3_env.machines_user_yml, yaml_file)

    # create localhost execution folder if it is not exists
    if not os.path.exists(os.path.join(FS3_env.FabSim3_PATH, "localhost_exe")):
        os.makedirs(os.path.join(FS3_env.FabSim3_PATH, "localhost_exe"))


def main():
    config_yml_files()

    # setup ssh localhost
    if os.path.isfile("{}/.ssh/id_rsa.pub".format(os.path.expanduser("~"))):
        print("local id_rsa key already exists.")
    else:
        os.system('ssh-keygen -q -f ~/.ssh/id_rsa -t rsa -b 4096 -N ""')

    os.system("cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys")
    os.system("chmod og-wx ~/.ssh/authorized_keys")
    os.system("ssh-keyscan -H localhost >> ~/.ssh/known_hosts")

    # use ssh-add instead of ssh-copy-id for MacOSX
    if FS3_env.OS_system == "OSX":
        os.system("ssh-add /Users/{}/.ssh/id_rsa".format(FS3_env.user_name))

    bash_scripts = [
        "~/.bashrc",
        "~/.bash_profile",
        "~/.zshrc",
        "~/.bash_aliases",
    ]
    title = "[orange_red1]Congratulation :clinking_beer_mugs:[/orange_red1]\n"
    msg = "[dark_cyan]FabSim3 installation was successful :heavy_check_mark:[/dark_cyan]\n\n"
    msg += "In order to use fabsim command anywhere in your PC, you need to "
    msg += "update the [blue]PATH[/blue] and [blue]PYTHONPATH[/blue] environmental variables.\n\n"
    msg += "\t[red1]export[/red1] [blue]PATH[/blue]={}/fabsim/bin:[blue]$PATH[/blue]\n".format(
        FS3_env.FabSim3_PATH
    )
    msg += "\t[red1]export[/red1] [blue]PYTHONPATH[/blue]={}:[blue]$PYTHONPATH[/blue]\n\n".format(
        FS3_env.FabSim3_PATH
    )
    
    # Check if ~/.local/bin is already in PATH
    local_bin_path = os.path.expanduser("~/.local/bin")
    if local_bin_path not in os.environ["PATH"]:
        msg += "\t[red1]export[/red1] [blue]PATH[/blue]=~/.local/bin:[blue]$PATH[/blue]\n"

    msg += "\nThe last list is added because the required packages are "
    msg += 'installed with flag "--user" which makes pip install packages '
    msg += "in your home directory instead of system directory."

    print(Panel.fit(msg, title=title, border_style="orange_red1"))

    title = "[dark_green]Tip[/dark_green]"
    msg = "\nTo make these updates permanent, you can add the export commands "
    msg += "above at the end of your bash shell script which could be one of "
    msg += "[{}] files, depends on your OS System.\n\n".format(
        ", ".join(
            [
                "[light_sea_green]{}[/light_sea_green]".format(name)
                for name in bash_scripts
            ]
        )
    )
    msg += ":bellhop_bell: To load the new updates in [blue]PATH[/blue] and [blue]PYTHONPATH[/blue] "
    msg += "you need to reload your bash shell script, e.g., "
    msg += (
        "[red1]source[/red1] [light_sea_green]~/.bashrc[/light_sea_green], or "
    )
    msg += "lunch a new terminal."

    print(Panel.fit(msg, title=title, border_style="dark_green"))

    # check if fabsim command is already available or not
    if which("fabsim") is not None:
        print("\n")
        print(
            Panel.fit(
                "fabsim [red1]command is already added to the [/red1][blue]PATH[/blue] "
                "[red1]variable. Please make sure you remove the old FabSim3 directory "
                "from your bash shell script.",
                title="[orange_red1]WARNING[/orange_red1]",
            )
        )
        
    # Set the FABSIM3_HOME environment variable
    os.environ["FABSIM3_HOME"] = FS3_env.FabSim3_PATH
    export_cmd = f'export FABSIM3_HOME="{FS3_env.FabSim3_PATH}"'

    # Check if the export command already exists in the shell configuration file
    shell_config_file = os.path.expanduser("~/.bashrc")  # Modify the file name if needed
    with open(shell_config_file, "r") as f:
        shell_config_content = f.read()
    if export_cmd not in shell_config_content:
        # Add the export command to the shell configuration file if it doesn't exist
        with open(shell_config_file, "a") as f:
            f.write("\n" + export_cmd + "\n")


if __name__ == "__main__":
    main()
