# FabSim3 Commands Python API
#
# This file maps command-line instructions for FabSim3 to Python functions.
# NOTE: No effort is made to map output back to FabSim, as this complicates
# the implementation greatly.
#
# This file can be included in any code base.
# It has no dependencies, but does require a working FabSim3 installation.

import os


def fabsim(command, arguments, machine='localhost'):
    """
    Generic function for running any FabSim3 command.

    Args:
        command (str): the FanSim3 command to execute
        arguments (str): a list of arguments, starting with the config ID,
          followed by keyword arguments "config,arg1=....,arg2=...."
        machine (str, optional): the name of the remote machine as indicated in
          machines_user.yml
    """
    print("Executing\n\n", "\tfabsim {} {}:{}".format(
        machine, command, arguments)
    )

    os.system("fabsim {} {}:{}".format(machine, command, arguments))


def fetch_results(machine="localhost"):
    """
    Retrieves the results from the remote machine, and stores it in the FabSim3
    results directory.

    Args:
        machine (str, optional): the name of the remote machine as indicated in
          machines_user.yml

    Returns:
        bool: a boolean flag, indicating success (True) or failure (False)
    """
    # TODO: check will this catch errors in fetch_results??
    try:
        fabsim("fetch_results", "", machine)
        return True
    except Exception:
        return False


def status(machine="localhost"):
    """
    Prints the status of the jobs running on the remote machine.

    Args:
        machine (str, optional): the name of the remote machine as indicated in
          machines_user.yml
    """
    fabsim("stat", "", machine)


def wait(machine='localhost', sleep=1):
    """
    Subroutine which returns when all jobs on the remote machine have finished.

    Args:
        machine (str, optional): the name of the remote machine as indicated in
          machines_user.yml
        sleep (int, optional): time interval in minutes between checks
    Returns:
        bool: if `False`, something went wrong

    """
    # number of header lines in fab <machine> stat
    header = 2
    finished = False

    while not finished:
        # get the output lines of fab <machine> stat
        try:
            out = subprocess.run(['fab', machine, 'stat'],
                                 stdout=subprocess.PIPE)
        except Exception:
            print('wait subroutine failed')
            return finished

        out = out.stdout.decode('utf-8').split("\n")
        # number of uncompleted runs
        n_uncompleted = 0
        print('Checking job status...')
        for i in range(header, len(out)):
            # remove all spaces from current line
            line = out[i].split()

            # line = '' means no Job ID, and if the number of uncompleted runs
            # is zero, we are done
            if len(line) == 0 and n_uncompleted == 0:
                print('All runs have completed')
                finished = True
                return finished
            # If the first entry is a number, we have found a running/pending
            # or completing job ID
            elif len(line) > 0 and line[0].isnumeric():
                print('Job %s is %s' % (line[0], line[1]))
                n_uncompleted += 1

        # no more jobs
        if n_uncompleted == 0:
            finished = True
            return finished
        # still active jobs, sleep
        else:
            time.sleep(sleep * 60)


def run_uq_ensemble(campaign_dir, script_name, machine="localhost", **kwargs):
    """
    Launches a UQ ensemble.
    """

    sim_ID = campaign_dir.split("/")[-1]
    arguments = "{},campaign_dir={},script_name={}".format(sim_ID,
                                                           campaign_dir,
                                                           script_name
                                                           )
    # add additional named arguments list
    if len(kwargs) > 0:
        arguments += ",{}".format(
            (",".join("%s=%s" % (arg_name, kwargs[arg_name])
                      for arg_name in kwargs)
             )
        )

    fabsim("run_uq_ensemble", arguments, machine=machine)


def get_uq_samples(campaign_dir, machine="localhost", **kwargs):
    """
    Retrieves results from UQ ensemble
    """
    sim_ID = campaign_dir.split("/")[-1]
    arguments = "{},campaign_dir={}".format(sim_ID,
                                            campaign_dir
                                            )

    # add additional named arguments list
    if len(kwargs) > 0:
        arguments += ",{}".format(
            (",".join("%s=%s" % (arg_name, kwargs[arg_name])
                      for arg_name in kwargs))
        )

    fabsim("get_uq_samples", arguments, machine=machine)
