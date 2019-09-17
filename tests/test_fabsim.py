import os
import sys
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '../base/')
#sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '../../base/')

from deploy.templates import *
from deploy.machines import *
from fabric.contrib.project import *
from base.fab import *

import fileinput

def test_fabsim():
    """
    The main FabSim3 test suite. Every test is captured in an assert statement.
    """
    assert("plugins" in get_plugin_path("FabDummy"))
    assert("FabDummy" in get_plugin_path("FabDummy"))
    assert(len(get_fabsim_git_hash()) > 0)

def test_fabdummy_install():
    assert( subprocess.call(["fab", "localhost", "install_plugin:FabDummy"]) == 0)

def test_fabsim_password_bugfix():
    """
    GitHub Issue #56
    """
    output = subprocess.check_output(["fab", "localhost", "dummy:dummy_test,password=ERROR,dumpenv=True"]).decode("utf-8")
    print(output)
    assert(output.find('\'password\': \'ERROR\'') < 0)


def test_fabdummy():
    assert( subprocess.call(["fab", "localhost", "dummy:dummy_test"]) == 0)
    output = subprocess.check_output(["fab", "localhost", "dummy:dummy_test"]).decode("utf-8")
    assert(output.find('success') >= 0)

def test_dummy_fabdummy_replicas():
    assert( subprocess.call(["fab", "localhost", "dummy:dummy_test,replicas=5"]) == 0)
    output = subprocess.check_output(["fab", "localhost", "dummy:dummy_test,replicas=5"]).decode("utf-8")
    assert(output.find('success') >= 0)
    
def test_dummy_ensemble():
    assert( subprocess.call(["fab", "localhost", "dummy_ensemble:dummy_test"]) == 0)
    output = subprocess.check_output(["fab", "localhost", "dummy_ensemble:dummy_test"]).decode("utf-8")
    assert(output.find('success') >= 0)

def test_dummy_ensemble_replicas():
    assert( subprocess.call(["fab", "localhost", "dummy_ensemble:dummy_test,replicas=5"]) == 0)
    output = subprocess.check_output(["fab", "localhost", "dummy_ensemble:dummy_test,replicas=5"]).decode("utf-8")
    assert(output.find('success') >= 0)    
