import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../base/')

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
