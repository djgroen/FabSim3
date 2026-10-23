import sys
from pathlib import Path

import pytest
import yaml

import configure_fabsim as cf


def make_env(path: Path, conda: bool = False) -> Path:
    """Create the minimal layout of a virtualenv/conda environment."""
    path.mkdir(parents=True)
    (path / "bin").mkdir()
    (path / "bin" / "python").write_text("")
    if conda:
        (path / "conda-meta").mkdir()
    else:
        (path / "pyvenv.cfg").write_text("home = /usr/bin\n")
    return path


@pytest.fixture
def no_active_env(monkeypatch):
    for name in ("VIRTUAL_ENV", "CONDA_PREFIX", "CONDA_DEFAULT_ENV"):
        monkeypatch.delenv(name, raising=False)
    # Use a neutral prefix so the tests do not depend on whether the test
    # runner itself is executed inside a venv or a conda environment.
    neutral_prefix = "/nonexistent/fabsim-test-base"
    monkeypatch.setattr(sys, "base_prefix", neutral_prefix)
    monkeypatch.setattr(sys, "prefix", neutral_prefix)
    return monkeypatch


def test_detect_active_env_returns_none(no_active_env):
    assert cf.detect_active_env() is None


def test_detect_active_env_from_running_interpreter(tmp_path, no_active_env):
    env = make_env(tmp_path / "env")
    no_active_env.setattr(sys, "prefix", str(env))

    info = cf.detect_active_env()

    assert info.path == env.resolve()
    assert info.kind == "venv"
    assert info.source == "interpreter"


def test_detect_active_env_from_virtual_env(tmp_path, no_active_env):
    env = make_env(tmp_path / "env")
    no_active_env.setenv("VIRTUAL_ENV", str(env))

    info = cf.detect_active_env()

    assert info.path == env.resolve()
    assert info.source == "VIRTUAL_ENV"


def test_detect_active_env_from_conda_prefix(tmp_path, no_active_env):
    env = make_env(tmp_path / "env", conda=True)
    no_active_env.setenv("CONDA_PREFIX", str(env))
    no_active_env.setenv("CONDA_DEFAULT_ENV", "fabsim-test")

    info = cf.detect_active_env()

    assert info.path == env.resolve()
    assert info.kind == "conda"
    assert info.source == "CONDA_PREFIX"


def test_detect_active_env_from_conda_interpreter(tmp_path, no_active_env):
    env = make_env(tmp_path / "env", conda=True)
    no_active_env.setattr(sys, "prefix", str(env))
    no_active_env.setattr(sys, "base_prefix", str(env))

    info = cf.detect_active_env()

    assert info.path == env.resolve()
    assert info.kind == "conda"
    assert info.source == "interpreter"


def test_prepare_prefers_active_environment(tmp_path, monkeypatch):
    root = tmp_path / "FabSim3"
    make_env(root / "VirtualEnv")
    active = make_env(tmp_path / "active")
    info = cf.AttributeDict(
        path=active.resolve(),
        python=str(active / "bin" / "python"),
        kind="venv",
        source="interpreter",
    )
    monkeypatch.setattr(cf, "detect_active_env", lambda: info)

    result = cf.prepare_python_environment(root)

    assert result.path == active.resolve()
    assert result.source == "interpreter"


def test_prepare_reuses_existing_project_environment(tmp_path, monkeypatch):
    root = tmp_path / "FabSim3"
    project_env = make_env(root / "VirtualEnv")
    monkeypatch.setattr(cf, "detect_active_env", lambda: None)

    result = cf.prepare_python_environment(root)

    assert result.path == project_env.resolve()
    assert result.source == "project"
    assert result.python == str(project_env / "bin" / "python")


def test_prepare_creates_project_environment_when_none_exists(
    tmp_path, monkeypatch
):
    root = tmp_path / "FabSim3"
    monkeypatch.setattr(cf, "detect_active_env", lambda: None)
    monkeypatch.setattr(cf, "create_virtualenv", make_env)

    result = cf.prepare_python_environment(root)

    assert result.path == (root / "VirtualEnv").resolve()
    assert result.source == "project"


def test_prepare_backs_up_invalid_project_environment(tmp_path, monkeypatch):
    root = tmp_path / "FabSim3"
    (root / "VirtualEnv").mkdir(parents=True)
    monkeypatch.setattr(cf, "detect_active_env", lambda: None)
    monkeypatch.setattr(cf, "create_virtualenv", make_env)

    cf.prepare_python_environment(root)

    backups = [
        path.name
        for path in root.iterdir()
        if path.name.startswith("VirtualEnv.bak.")
    ]
    assert len(backups) == 1


def test_install_module_uses_target_interpreter(monkeypatch):
    calls = []
    monkeypatch.setattr(cf, "_module_available", lambda *args: False)
    monkeypatch.setattr(
        cf.subprocess,
        "check_call",
        lambda command: calls.append(command),
    )

    status = cf.install_module("rich", "rich", "/tmp/target/python")

    assert status == "installed"
    assert calls == [["/tmp/target/python", "-m", "pip", "install", "rich"]]


def test_install_module_reports_already_installed(monkeypatch):
    monkeypatch.setattr(cf, "_module_available", lambda *args: True)

    status = cf.install_module("rich", "rich", "/tmp/target/python")

    assert status == "already"


def test_setup_yaml_config_records_active_environment(
    tmp_path, monkeypatch
):
    deploy = tmp_path / "fabsim" / "deploy"
    deploy.mkdir(parents=True)
    (deploy / "machines_user_example.yml").write_text(
        "default:\n  username: example\n"
        "localhost:\n  username: example\n"
    )
    env = make_env(tmp_path / "env")
    monkeypatch.setattr(cf, "get_venv_python", lambda path: sys.executable)

    assert cf.setup_yaml_config(env, tmp_path)

    data = yaml.safe_load((deploy / "machines_user.yml").read_text())
    assert data["localhost"]["virtual_env_path"] == str(env)
    assert data["localhost"]["venv"] is True


def test_setup_yaml_config_without_environment(tmp_path, monkeypatch):
    deploy = tmp_path / "fabsim" / "deploy"
    deploy.mkdir(parents=True)
    (deploy / "machines_user_example.yml").write_text(
        "default:\n  username: example\n"
        "localhost:\n  username: example\n"
    )
    monkeypatch.setattr(cf, "get_venv_python", lambda path: sys.executable)

    assert cf.setup_yaml_config(None, tmp_path)

    data = yaml.safe_load((deploy / "machines_user.yml").read_text())
    assert data["localhost"]["virtual_env_path"] == ""
    assert "venv" not in data["localhost"]
