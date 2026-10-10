import os
import re
import sys
import subprocess
import platform
import getpass
from shutil import which
from pathlib import Path
import venv
import importlib
from pprint import pprint

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich import print
except ImportError:
    Console = None
    Panel = None
    print = print

console = Console() if Console else None


_ANSI_STYLES = {
    "black": "30",
    "red": "31",
    "red1": "31",
    "green": "32",
    "dark_green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "dark_cyan": "36",
    "light_sea_green": "36",
    "white": "37",
    "orange_red1": "38;5;202",
}

_MARKUP_RE = re.compile(r"\[(/?)([A-Za-z0-9_]+(?: +[A-Za-z0-9_]+)*)\]")

_COLOR_SUPPORTED = (
    hasattr(sys.stdout, "isatty")
    and sys.stdout.isatty()
    and os.environ.get("NO_COLOR") is None
    and os.environ.get("TERM", "") != "dumb"
    and (os.name != "nt" or "WT_SESSION" in os.environ or "ANSICON" in os.environ)
)


def render_markup(text: str) -> str:
    """Render a small subset of rich markup using ANSI escape codes.

    This lets FabSim3 print coloured output on both Linux and macOS even
    when ``rich`` is not installed, instead of dumping the raw ``[tag]``
    sequences. Colour is disabled automatically for non-interactive output
    (pipes, CI) or when ``NO_COLOR`` is set.
    """
    def _tag(match):
        if not _COLOR_SUPPORTED:
            return ""
        closing, tag = match.group(1), match.group(2)
        if closing:
            return "\033[0m"
        codes = []
        for token in tag.split():
            if token == "bold":
                codes.append("1")
            elif token in _ANSI_STYLES:
                codes.append(_ANSI_STYLES[token])
        return "\033[{}m".format(";".join(codes)) if codes else ""

    return _MARKUP_RE.sub(_tag, text)


def _emit(message: str, title: str = None, border_style: str = "orange_red1"):
    """Print a message using rich when available, ANSI colours otherwise."""
    if console:
        if title is not None:
            console.print(Panel.fit(message, title=title, border_style=border_style))
        else:
            console.print(message)
        return
    rendered = render_markup(message)
    if title is not None:
        rendered = render_markup(title) + "\n" + rendered
    print(rendered)


class AttributeDict(dict):
    def __getattr__(self, key): return self[key]
    def __setattr__(self, key, value): self[key] = value
    def __delattr__(self, key): del self[key]


def get_platform_info():
    system = platform.system()
    return {
        "OS_system": system,
        "OS_release": platform.release(),
        "OS_version": platform.version(),
        "FabSim3_PATH": Path(__file__).resolve().parent,
        "user_name": getpass.getuser(),
        "venv_path": None,
        "machines_user_yml": None
    }


FS3_env = AttributeDict(get_platform_info())

def create_virtualenv(path: Path) -> Path:
    if path.exists():
        _print_activation_reminder(path)
        return path

    print(f"Creating virtual environment at: {path}")
    try:
        venv.create(path, with_pip=True)
        _print_activation_success(path)
        return path
    except Exception as e:
        print(f"Failed to create venv: {e}")
        return None


def _print_activation_reminder(venv_path: Path):
    activate_cmd = get_activation_command(venv_path)
    msg = f"[yellow]Virtual environment already exists.[/yellow]\n[cyan]{activate_cmd}[/cyan]"
    _emit(msg, title="[green]Virtual Environment[/green]")


def _print_activation_success(venv_path: Path):
    activate_cmd = get_activation_command(venv_path)
    msg = f"[green]Virtual environment created![/green]\nActivate: [cyan]{activate_cmd}[/cyan]"
    _emit(msg, title="[blue]Setup Success[/blue]")


def get_activation_command(venv_path: Path):
    if platform.system() == "Windows":
        return str(venv_path / "Scripts" / "activate")
    return f"source {venv_path}/bin/activate"


def get_shell_config_file() -> Path:
    """Return the shell startup file for the user's current shell.

    On macOS the default login shell is zsh, so ~/.bashrc usually does not
    exist. We detect the shell from $SHELL and fall back to a sensible
    default that will be created if it is missing.
    """
    home = Path.home()
    shell = os.environ.get("SHELL", "").lower()

    if "zsh" in shell:
        candidates = [home / ".zshrc"]
    elif "bash" in shell:
        if platform.system() == "Darwin":
            candidates = [home / ".bash_profile", home / ".bashrc"]
        else:
            candidates = [home / ".bashrc"]
    elif "fish" in shell:
        candidates = [home / ".config" / "fish" / "config.fish"]
    else:
        candidates = [home / ".profile"]

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def get_venv_python(venv_path: Path) -> str:
    if venv_path is None:
        return "python3"
    if platform.system() == "Windows":
        return str(venv_path / "Scripts" / "python.exe")
    return str(venv_path / "bin" / "python")


def install_module(pkg: str, pip_name: str = None, venv_path: Path = None) -> bool:
    pip_name = pip_name or pkg
    
    if venv_path is None:
        # No venv - install to current environment with --user
        try:
            importlib.import_module(pkg)
            return True
        except ImportError:
            install_cmd = ["python3", "-m", "pip", "install", "--user", pip_name]
            if pip_name == "fabric2":
                install_cmd.append("invoke==2.2.0")
            
            print(f"Installing {pkg} package...")
            try:
                subprocess.check_call(install_cmd)
                return False  # Just installed
            except subprocess.CalledProcessError as e:
                print(f"Failed to install {pkg}: {e}")
                return False
    else:
        # Check if package is installed in the virtual environment
        python_exe = get_venv_python(venv_path)
        
        # Test if package is available in the venv
        check_cmd = [python_exe, "-c", f"import {pkg}"]
        try:
            subprocess.run(check_cmd, check=True, capture_output=True)
            return True  # Already installed in venv
        except subprocess.CalledProcessError:
            # Package not in venv, install it
            install_cmd = [python_exe, "-m", "pip", "install", pip_name]
            if pip_name == "fabric2":
                install_cmd.append("invoke==2.2.0")
            
            print(f"Installing {pkg} package in virtual environment...")
            try:
                subprocess.check_call(install_cmd)
                return False  # Just installed
            except subprocess.CalledProcessError as e:
                print(f"Failed to install {pkg} in venv: {e}")
                return False


def setup_yaml_in_venv(venv_path: Path, fabsim_path: Path):
    """Run YAML setup in the virtual environment"""
    if venv_path is None:
        return setup_yaml_local(fabsim_path)
    
    python_exe = get_venv_python(venv_path)
    script_content = f'''
import sys
sys.path.insert(0, "{fabsim_path}")
import ruamel.yaml
from pathlib import Path

yaml = ruamel.yaml.YAML()
yaml.allow_duplicate_keys = None
yaml.preserve_quotes = True
yaml.width = 4096

path = Path("{fabsim_path}")
venv_path = Path("{venv_path}") 
yml_path = path / "fabsim" / "deploy" / "machines_user_example.yml"
with open(yml_path) as f:
    data = yaml.load(f)

# Update paths
exe_path = path / "localhost_exe"
config_path = path / "config_files"
result_path = path / "results"

S = ruamel.yaml.scalarstring.DoubleQuotedScalarString
import getpass
user = getpass.getuser()

for key in ["localhost", "default"]:
    data[key]["home_path_template"] = S(str(exe_path))
    data[key]["username"] = user
    
data["default"]["virtual_env_path"] = str(venv_path)
data["localhost"]["virtual_env_path"] = str(venv_path)

data["default"]["local_configs"] = str(config_path)
data["default"]["local_results"] = str(result_path)

machines_yml = path / "fabsim" / "deploy" / "machines_user.yml"
if machines_yml.exists():
    backup = machines_yml.with_name("machines_user_backup.yml")
    machines_yml.rename(backup)
    print("Backed up existing machines_user.yml to machines_user_backup.yml")

with open(machines_yml, "w") as f:
    yaml.dump(data, f)
print("Created machines_user.yml with user-specific configurations")
print(f"Set virtual_env_path to: {{venv_path}}")

# Create directories
exe_path.mkdir(exist_ok=True)
config_path.mkdir(exist_ok=True)
result_path.mkdir(exist_ok=True)
print("Created directories: localhost_exe, config_files, results")
'''
    
    try:
        result = subprocess.run([python_exe, "-c", script_content], 
                               capture_output=True, text=True, check=True)
        print(result.stdout)
        
        # Double-check that the file was actually created
        machines_yml_path = fabsim_path / "fabsim" / "deploy" / "machines_user.yml"
        if not machines_yml_path.exists():
            print("ERROR: machines_user.yml was not created successfully!")
            print("FabSim3 cannot function without this critical configuration file.")
            sys.exit(1)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"CRITICAL ERROR: Failed to set up YAML configuration: {e}")
        print(f"stderr: {e.stderr}")
        print("FabSim3 setup cannot continue without machines_user.yml")
        sys.exit(1)

def main():
    FS3_env["venv_path"] = create_virtualenv(FS3_env["FabSim3_PATH"] / "VirtualEnv")

    required = {
        "wheel": None,
        "setuptools": None,
        "rich": "rich",
        "ruamel.yaml": None,
        "numpy": None,
        "yaml": "pyyaml",
        "fabric2": "fabric2",
        "beartype": "beartype",
    }

    for pkg, pip_name in required.items():
        installed = install_module(pkg, pip_name, FS3_env["venv_path"])
        status = "already" if installed else "just"
        color = "green" if installed else "yellow"
        _emit(f"[{color}]Package {pkg} {status} installed[/{color}]")

    # Set up YAML configuration files using the virtual environment
    if not setup_yaml_in_venv(FS3_env["venv_path"], FS3_env["FabSim3_PATH"]):
        print("Failed to set up configuration files")

    # setup ssh localhost
    if os.path.isfile("{}/.ssh/id_rsa.pub".format(os.path.expanduser("~"))):
        print("local id_rsa key already exists.")
    else:
        os.system('ssh-keygen -q -f ~/.ssh/id_rsa -t rsa -b 4096 -N ""')

    os.system("cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys")
    os.system("chmod og-wx ~/.ssh/authorized_keys")
    os.system("ssh-keyscan -H localhost >> ~/.ssh/known_hosts")

    # use ssh-add instead of ssh-copy-id for MacOSX
    if FS3_env.OS_system == "Darwin":  # macOS returns "Darwin", not "OSX"
        os.system("ssh-add /Users/{}/.ssh/id_rsa".format(FS3_env.user_name))

    bash_scripts = [
        "~/.bashrc",
        "~/.bash_profile", 
        "~/.zshrc",
        "~/.bash_aliases",
    ]
    title = "[orange_red1]Congratulation[/orange_red1]\n"
    msg = "[dark_cyan]FabSim3 installation was successful.[/dark_cyan]\n\n"
    
    # Add virtual environment information
    if FS3_env.venv_path:
        activate_cmd = get_activation_command(FS3_env.venv_path)
        msg += "[yellow]Virtual Environment Setup Complete![/yellow]\n"
        msg += f"[green]Activate your virtual environment:[/green] [bold cyan]{activate_cmd}[/bold cyan]\n\n"
    
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

    _emit(msg, title=title, border_style="orange_red1")

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
    msg += "To load the new updates in [blue]PATH[/blue] and [blue]PYTHONPATH[/blue] "
    msg += "you need to reload your shell script, e.g., "
    msg += (
        "[red1]source[/red1] [light_sea_green]{}[/light_sea_green], or ".format(
            "~/" + str(get_shell_config_file().relative_to(Path.home()))
        )
    )
    msg += "launch a new terminal."

    _emit(msg, title=title, border_style="dark_green")

    # check if fabsim command is already available or not
    if which("fabsim") is not None:
        warning_msg = ("fabsim command is already added to the PATH variable. "
                      "Please make sure you remove the old FabSim3 directory "
                      "from your bash shell script.")
        _emit(warning_msg, title="[orange_red1]WARNING[/orange_red1]")
        
    # Set the FABSIM3_HOME environment variable
    os.environ["FABSIM3_HOME"] = str(FS3_env.FabSim3_PATH)  # Convert Path to string
    export_cmd = f'export FABSIM3_HOME="{FS3_env.FabSim3_PATH}"'

    # Check if the export command already exists in the shell configuration file
    shell_config_file = get_shell_config_file()
    try:
        shell_config_content = (
            shell_config_file.read_text() if shell_config_file.exists() else ""
        )
        if export_cmd not in shell_config_content:
            shell_config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(shell_config_file, "a") as f:
                f.write("\n" + export_cmd + "\n")
            print(f"Added FABSIM3_HOME export to {shell_config_file}")
        else:
            print(f"FABSIM3_HOME export already present in {shell_config_file}")
    except OSError as e:
        print(f"Warning: Could not update shell configuration file {shell_config_file}: {e}")

    print("FabSim3 setup complete.")


if __name__ == "__main__":
    main()