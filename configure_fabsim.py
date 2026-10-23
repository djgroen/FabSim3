import os
import re
import sys
import subprocess
import platform
import getpass
from datetime import datetime
from shutil import which
from pathlib import Path
import venv
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


def _python_in_env(env_path):
    """Return the Python executable inside an environment, if present.

    The location differs between venv/virtualenv (``bin/python`` or
    ``Scripts/python.exe``) and conda (``python.exe`` in the prefix root on
    Windows), so look for the actual executable instead of assuming a layout.
    """
    if env_path is None:
        return None

    env_path = Path(env_path)
    if os.name == "nt":
        candidates = [env_path / "Scripts" / "python.exe", env_path / "python.exe"]
    else:
        candidates = [env_path / "bin" / "python", env_path / "bin" / "python3"]

    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


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
    """Return the Python interpreter for an environment.

    If no environment path is given, the interpreter running this script is
    used. This keeps the no-environment fallback independent of how ``python``
    or ``python3`` happens to be installed.
    """
    if venv_path is None:
        return sys.executable or "python3"

    python_exe = _python_in_env(venv_path)
    if python_exe is not None:
        return str(python_exe)

    if os.name == "nt":
        return str(Path(venv_path) / "Scripts" / "python.exe")
    return str(Path(venv_path) / "bin" / "python")


def _is_conda_env(path: Path) -> bool:
    return (Path(path) / "conda-meta").is_dir()


def _is_valid_project_env(path: Path) -> bool:
    """Check that ``path`` is an environment FabSim3 can safely reuse."""
    path = Path(path)
    if not path.is_dir():
        return False
    has_marker = (path / "pyvenv.cfg").is_file() or _is_conda_env(path)
    return has_marker and _python_in_env(path) is not None


def detect_active_env():
    """Return the Python environment the user has activated, if any.

    The result is an ``AttributeDict`` with ``path``, ``python``, ``kind`` and
    ``source`` keys, or ``None`` when no environment is active.

    ``sys.prefix`` is checked first because it describes the interpreter that
    is actually running the installer. The shell variables are only a fallback
    for the case where the script was started by a different interpreter (for
    example ``/usr/bin/python3 configure_fabsim.py`` inside an activated env).
    """
    def _from_prefix(prefix, source):
        path = Path(prefix).expanduser().resolve()
        python_exe = _python_in_env(path)
        if python_exe is None:
            return None

        kind = "conda" if _is_conda_env(path) else "venv"
        return AttributeDict(
            path=path,
            python=str(python_exe),
            kind=kind,
            source=source,
        )

    base_prefix = getattr(
        sys,
        "base_prefix",
        getattr(sys, "real_prefix", sys.prefix),
    )
    running_prefix = Path(sys.prefix)
    if sys.prefix != base_prefix or _is_conda_env(running_prefix):
        info = _from_prefix(sys.prefix, "interpreter")
        if info is not None:
            return info

    virtual_env = os.environ.get("VIRTUAL_ENV")
    if virtual_env:
        info = _from_prefix(virtual_env, "VIRTUAL_ENV")
        if info is not None:
            return info

    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix:
        info = _from_prefix(conda_prefix, "CONDA_PREFIX")
        if info is not None:
            return info

    return None


def _is_conda_base(env_info) -> bool:
    return (
        env_info.kind == "conda"
        and os.environ.get("CONDA_DEFAULT_ENV") == "base"
    )


def prepare_python_environment(fabsim_path: Path):
    """Choose the Python environment automatically.

    Priority:
      1. the environment the user has already activated,
      2. an existing, valid ``FabSim3/VirtualEnv``,
      3. create ``FabSim3/VirtualEnv``.
    """
    project_env = (Path(fabsim_path) / "VirtualEnv").resolve()
    active = detect_active_env()

    if active is not None:
        if active.path == project_env:
            _emit(
                f"[green]Using active virtual environment:[/green] "
                f"[cyan]{active.path}[/cyan]"
            )
        else:
            if project_env.exists():
                _emit(
                    f"[green]Detected active virtual environment:[/green] "
                    f"[cyan]{active.path}[/cyan]\n"
                    f"Using it and ignoring the existing "
                    f"[cyan]{project_env}[/cyan]."
                )
            else:
                _emit(
                    f"[green]Detected active virtual environment:[/green] "
                    f"[cyan]{active.path}[/cyan]\n"
                    f"Using it instead of creating FabSim3/VirtualEnv."
                )

            if active.source != "interpreter":
                _emit(
                    f"[yellow]Note:[/yellow] the environment was detected from "
                    f"[cyan]{active.source}[/cyan], so its Python will be used "
                    f"instead of the interpreter that started this script."
                )

        if _is_conda_base(active):
            _emit(
                "[yellow]Warning:[/yellow] FabSim3 is using the conda "
                "[cyan]base[/cyan] environment. Installing into it can affect "
                "other projects; consider activating a dedicated environment."
            )
        return active

    if project_env.exists():
        if _is_valid_project_env(project_env):
            _emit(
                f"[green]No active environment detected.[/green]\n"
                f"Reusing existing [cyan]{project_env}[/cyan]."
            )
            return AttributeDict(
                path=project_env,
                python=get_venv_python(project_env),
                kind="venv",
                source="project",
            )

        backup = project_env.with_name(
            f"{project_env.name}.bak."
            f"{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )
        try:
            project_env.rename(backup)
        except OSError as e:
            _emit(
                f"[red]Could not move the invalid environment "
                f"[cyan]{project_env}[/cyan]: {e}[/red]"
            )
            return AttributeDict(
                path=None,
                python=sys.executable,
                kind="system",
                source="fallback",
            )
        _emit(
            f"[yellow]The existing [cyan]{project_env}[/cyan] is not a valid "
            f"Python environment. It was moved to [cyan]{backup}[/cyan].[/yellow]"
        )

    _emit(
        f"[cyan]No active environment detected.[/cyan]\n"
        f"Creating [cyan]{project_env}[/cyan]."
    )
    created = create_virtualenv(project_env)
    if created is None:
        _emit(
            "[red]Could not create a virtual environment.[/red]\n"
            f"Falling back to the interpreter running this script: "
            f"[cyan]{sys.executable}[/cyan]"
        )
        return AttributeDict(
            path=None,
            python=sys.executable,
            kind="system",
            source="fallback",
        )

    return AttributeDict(
        path=Path(created),
        python=get_venv_python(created),
        kind="venv",
        source="project",
    )


def _module_available(python_exe: str, pkg: str) -> bool:
    try:
        subprocess.run(
            [python_exe, "-c", f"import {pkg}"],
            check=True,
            capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, OSError):
        return False


def _pip_available(python_exe: str) -> bool:
    try:
        subprocess.run(
            [python_exe, "-m", "pip", "--version"],
            check=True,
            capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, OSError):
        return False


def install_module(
    pkg: str,
    pip_name: str = None,
    python_exe: str = None,
    use_user_site: bool = False,
) -> str:
    """Install a package into ``python_exe`` when it is not already importable.

    Returns ``"already"``, ``"installed"`` or ``"failed"`` so callers can
    report the real outcome.
    """
    pip_name = pip_name or pkg
    python_exe = python_exe or sys.executable

    if _module_available(python_exe, pkg):
        return "already"

    install_cmd = [python_exe, "-m", "pip", "install"]
    if use_user_site:
        install_cmd.append("--user")
    install_cmd.append(pip_name)
    if pip_name == "fabric2":
        install_cmd.append("invoke==2.2.0")

    print(f"Installing {pkg} package...")
    try:
        subprocess.check_call(install_cmd)
        return "installed"
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {pkg}: {e}")
        return "failed"


def setup_yaml_config(venv_path: Path, fabsim_path: Path):
    """Create machines_user.yml using the selected Python interpreter.

    ``venv_path`` may be ``None`` when no virtual environment could be
    created; in that case the current interpreter is used and the
    ``virtual_env_path`` entries are left empty.
    """
    python_exe = get_venv_python(venv_path)
    venv_path_str = str(venv_path) if venv_path else ""
    script_content = f'''
import sys
sys.path.insert(0, {str(fabsim_path)!r})
import ruamel.yaml
from pathlib import Path

yaml = ruamel.yaml.YAML()
yaml.allow_duplicate_keys = None
yaml.preserve_quotes = True
yaml.width = 4096

path = Path({str(fabsim_path)!r})
venv_path = Path({venv_path_str!r}) if {venv_path_str!r} else None
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

if venv_path is not None:
    data["default"]["virtual_env_path"] = str(venv_path)
    data["localhost"]["virtual_env_path"] = str(venv_path)
    # Make local job scripts activate the selected environment.
    data["localhost"]["venv"] = True
else:
    data["default"]["virtual_env_path"] = ""
    data["localhost"]["virtual_env_path"] = ""

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
print(f"Set virtual_env_path to: {{venv_path or ''}}")

# Create directories
exe_path.mkdir(exist_ok=True)
config_path.mkdir(exist_ok=True)
result_path.mkdir(exist_ok=True)
print("Created directories: localhost_exe, config_files, results")
'''

    try:
        result = subprocess.run(
            [python_exe, "-c", script_content],
            capture_output=True,
            text=True,
            check=True,
        )
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
    env_info = prepare_python_environment(FS3_env["FabSim3_PATH"])
    FS3_env["venv_path"] = env_info.path
    FS3_env["venv_python"] = env_info.python
    FS3_env["venv_active"] = env_info.source in (
        "interpreter",
        "VIRTUAL_ENV",
        "CONDA_PREFIX",
    )

    python_exe = FS3_env["venv_python"]
    if not _pip_available(python_exe):
        print(f"pip is not available for {python_exe}; trying to bootstrap it...")
        try:
            subprocess.check_call([python_exe, "-m", "ensurepip", "--upgrade"])
        except (subprocess.CalledProcessError, OSError) as e:
            _emit(
                f"[red]pip is not available for {python_exe}.[/red]\n"
                f"Please install pip in that environment and run the installer "
                f"again.\n[red]{e}[/red]"
            )
            sys.exit(1)

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

    failures = []
    for pkg, pip_name in required.items():
        status = install_module(
            pkg,
            pip_name,
            python_exe,
            use_user_site=FS3_env["venv_path"] is None,
        )
        if status == "already":
            _emit(f"[green]Package {pkg} is already installed[/green]")
        elif status == "installed":
            _emit(f"[yellow]Package {pkg} installed[/yellow]")
        else:
            failures.append(pkg)
            _emit(f"[red]Failed to install package {pkg}[/red]")

    if failures:
        _emit(
            "[red]These packages could not be installed:[/red] "
            + ", ".join(failures)
        )

    # Set up YAML configuration files using the selected environment
    if not setup_yaml_config(FS3_env["venv_path"], FS3_env["FabSim3_PATH"]):
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
    if FS3_env["venv_active"]:
        msg += (
            "[yellow]Using your active virtual environment:[/yellow] "
            f"[bold cyan]{FS3_env['venv_path']}[/bold cyan]\n\n"
        )
    elif FS3_env["venv_path"]:
        activate_cmd = get_activation_command(FS3_env["venv_path"])
        msg += "[yellow]Virtual Environment Setup Complete![/yellow]\n"
        msg += (
            "[green]Activate your virtual environment:[/green] "
            f"[bold cyan]{activate_cmd}[/bold cyan]\n\n"
        )
    else:
        msg += (
            "[yellow]No virtual environment is in use.[/yellow]\n"
            "The required packages were installed into the current Python "
            "environment.\n\n"
        )

    msg += "In order to use fabsim command anywhere in your PC, you need to "
    msg += "update the [blue]PATH[/blue] and [blue]PYTHONPATH[/blue] environmental variables.\n\n"
    msg += "\t[red1]export[/red1] [blue]PATH[/blue]={}/fabsim/bin:[blue]$PATH[/blue]\n".format(
        FS3_env.FabSim3_PATH
    )
    msg += "\t[red1]export[/red1] [blue]PYTHONPATH[/blue]={}:[blue]$PYTHONPATH[/blue]\n\n".format(
        FS3_env.FabSim3_PATH
    )

    # The --user fallback is only used when no environment is available.
    if FS3_env["venv_path"] is None:
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
        warning_msg = (
            "fabsim command is already added to the PATH variable. "
            "Please make sure you remove the old FabSim3 directory "
            "from your bash shell script."
        )
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
