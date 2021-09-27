import os
import sys
import subprocess
# from fabric.contrib.project import *
from fabsim.deploy.templates import *
from fabsim.deploy.machines import *
from fabsim.base.fab import *

import fileinput


def test_fabsim():
    """
    The main FabSim3 test suite. Every test is captured in an assert statement.
    """
    assert("plugins" in get_plugin_path("FabDummy"))
    assert("FabDummy" in get_plugin_path("FabDummy"))
    # assert(len(get_fabsim_git_hash()) > 0)


def test_fabdummy_install():
    assert(subprocess.call(
        ["fabsim", "localhost", "install_plugin:FabDummy"]) == 0)


def test_fabdummy_without_manual_ssh():
    assert(subprocess.call(
        ["fabsim", "localhost", "dummy:dummy_test,manual_ssh=false"]) == 0)
    output = subprocess.check_output(
        ["fabsim", "localhost", "dummy:dummy_test,manual_ssh=false"]).decode("utf-8")
    assert(output.find('success') >= 0)


def test_fabdummy_with_manual_ssh():
    assert(subprocess.call(
        ["fabsim", "localhost", "dummy:dummy_test,manual_ssh=true"]) == 0)
    output = subprocess.check_output(
        ["fabsim", "localhost", "dummy:dummy_test,manual_ssh=true"]).decode("utf-8")
    assert(output.find('success') >= 0)


def test_dummy_fabdummy_replicas_without_manual_ssh():
    assert(subprocess.call(
        ["fabsim", "localhost", "dummy:dummy_test,replicas=5,nb_process=2,manual_ssh=false"]) == 0)
    output = subprocess.check_output(
        ["fabsim", "localhost", "dummy:dummy_test,replicas=5,nb_process=2,manual_ssh=false"]).decode("utf-8")
    assert(output.find('success') >= 0)


def test_dummy_fabdummy_replicas_with_manual_ssh():
    assert(subprocess.call(
        ["fabsim", "localhost", "dummy:dummy_test,replicas=5,nb_process=2,manual_ssh=true"]) == 0)
    output = subprocess.check_output(
        ["fabsim", "localhost", "dummy:dummy_test,replicas=5,nb_process=2,manual_ssh=true"]).decode("utf-8")
    assert(output.find('success') >= 0)


def test_dummy_ensemble_without_manual_ssh():
    assert(subprocess.call(
        ["fabsim", "localhost", "dummy_ensemble:dummy_test,nb_process=2,manual_ssh=false"]) == 0)
    output = subprocess.check_output(
        ["fabsim", "localhost", "dummy_ensemble:dummy_test,nb_process=2,manual_ssh=false"]).decode("utf-8")
    assert(output.find('success') >= 0)


def test_dummy_ensemble_with_manual_ssh():
    assert(subprocess.call(
        ["fabsim", "localhost", "dummy_ensemble:dummy_test,nb_process=2,manual_ssh=true"]) == 0)
    output = subprocess.check_output(
        ["fabsim", "localhost", "dummy_ensemble:dummy_test,nb_process=2,manual_ssh=true"]).decode("utf-8")
    assert(output.find('success') >= 0)


def test_dummy_ensemble_replicas_without_manual_ssh():
    assert(subprocess.call(
        ["fabsim", "localhost", "dummy_ensemble:dummy_test,replicas=5,nb_process=2,manual_ssh=false"]) == 0)
    output = subprocess.check_output(
        ["fabsim", "localhost", "dummy_ensemble:dummy_test,replicas=5,nb_process=2,manual_ssh=false"]).decode("utf-8")
    assert(output.find('success') >= 0)


def test_dummy_ensemble_replicas_with_manual_ssh():
    assert(subprocess.call(
        ["fabsim", "localhost", "dummy_ensemble:dummy_test,replicas=5,nb_process=2,manual_ssh=true"]) == 0)
    output = subprocess.check_output(
        ["fabsim", "localhost", "dummy_ensemble:dummy_test,replicas=5,nb_process=2,manual_ssh=true"]).decode("utf-8")
    assert(output.find('success') >= 0)
