#
# This source file is part of the FabSim software toolkit, which is
# distributed under the BSD 3-Clause license.
# Please refer to LICENSE for detailed information regarding the licensing.
#
# fabfile.py is the main FabSim interface file.
# Here one can freely include or omit subsections of the FabSim toolkit,
# to modify the enabled functionalities.

import yaml
import importlib
import os
from pprint import pprint
try:
    from fabsim.base.fab import *
except ImportError:
    # update system PATH if FabSim3 directory did not added
    # to system PYTHONPATH
    import sys
    FabSim3_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, FabSim3_PATH)
    # Now, we can import fabsim APIs
    from fabsim.base.fab import *


config = yaml.load(
    open(os.path.join(env.fabsim_root, "deploy", "plugins.yml")),
    Loader=yaml.SafeLoader
)

for key in config.keys():
    plugin = {}
    try:
        plugin = importlib.import_module("plugins.{}.{}".format(key, key))
        plugin_dict = plugin.__dict__
        try:
            to_import = plugin.__all__
        except AttributeError:
            to_import = [name for name in plugin_dict
                         if not name.startswith("_")]
        globals().update({name: plugin_dict[name] for name in to_import})
        env.localplugins[key] = os.path.join(
            os.path.dirname(env.fabsim_root), "plugins", key
        )
    except ImportError as e:
        pass
