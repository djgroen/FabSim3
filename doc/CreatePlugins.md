# Creating a new plugin.

## Basic steps

* Fork FabDummy (https://www.github.com/djgroen/FabDummy)
* Rename the repository, and modify it to suit your own needs as you see fit.
* Rename FabDummy.py to the <name of your plugin>.py.
* In your new plugin repository, at the top of the <name of your plugin>.py, change `add_local_paths("FabDummy")` to `add_local_paths(<name of your plugin>)`.
* In the *main* FabSim3 repository, add an entry for your new plugin in `deploy/plugins.yml`.
* Set up your plugin using `fab localhost install_plugin:<name of your plugin>.
* You're good to go, although you'll inevitably will have to debug some of your modifications made in the second step of course :).

## Examples

For examples, see the plugins available in deploy/plugins.yml. 
FabDummy and FabMD are particularly good examples.
