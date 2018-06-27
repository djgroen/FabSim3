from deploy.templates import *
from deploy.machines import *
from fabric.contrib.project import *
from base.fab import *

import fileinput
import sys

@task
def test():
  """
  Run FabSim3 Unit Tests.
  """

  assert("plugins" in get_plugin_path("FabDummy"))
  assert("FabDummy" in get_plugin_path("FabDummy"))

  assert(len(get_fabsim_git_hash()) > 0)

  print("----------------------------------------")
  print("ALL FabSim3 BASE UNIT TESTS HAVE PASSED.")
