# FabSim3 Commands Python API
#
# This file maps command-line instructions for FabSim3 to Python functions.
# NOTE: No effort is made to map output back to FabSim, as this complicates
# the implementation greatly.
#
# This file can be included in any code base. 
# It has no dependencies, but does require a working FabSim3 installation.


def fabsim(machine = 'localhost', command, arguments):
    """
    Generic function for running any FabSim3 command.
    """
    os.system("fabsim {} {}:{}".format(machine, command, arguments)


def run_uq_ensemble(campaign_dir, script_name, machine='localhost'):
    """
    Launches a UQ ensemble.
    """
    sim_ID = campaign_dir.split('/')[-1]
    arguments = "{},campaign_dir={},script_name={}".format(sim_ID, campaign_dir, script_name)
    fabsim(machine, "run_uq_ensemble", arguments)
