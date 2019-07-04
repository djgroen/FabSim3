#
# This source file is part of the FabSim software toolkit, which is distributed under the BSD 3-Clause license.
# Please refer to LICENSE for detailed information regarding the licensing.
#
# fabfile.py is the main FabSim interface file. Here one can freely include or omit subsections of the FabSim toolkit,
# to modify the enabled functionalities.

import yaml
import importlib

from base.fab import *

config = yaml.load(open(os.path.join(env.localroot, 'deploy', 'plugins.yml')), Loader=yaml.SafeLoader)
for key in config.keys():
    plugin = {}
    try:
        plugin = importlib.import_module('plugins.{}.{}'.format(key, key))
        plugin_dict = plugin.__dict__
        try:
            to_import = plugin.__all__
        except AttributeError:
            to_import = [name for name in plugin_dict if not name.startswith('_')]
        globals().update({name: plugin_dict[name] for name in to_import})
        env.localplugins[key] = os.path.join(env.localroot, 'plugins', key)
    except ImportError:
        pass

