from deploy.templates import *
from deploy.machines import *
from fabric.contrib.project import *
import time


@task
def stat():
    """Check the remote message queue status. Syntax: fab <machine> stat."""
    # TODO: Respect varying remote machine queue systems.
    if not env.get('stat_postfix'):
        return run(template("$stat -u $username"))
    return run(template("$stat -u $username $stat_postfix"))


@task
def cancel(jobid=""):
    """Cancel a remote job. Syntax: fab <machine>
    cancel:jobid=<machine_specific_identifier_of_job>."""
    env.jobid = jobid
    return run(template("$cancel_job_command $jobid"))


@task
def monitor():
    """Report on the queue status, ctrl-C to interrupt.
    Syntax: fab <machine> monitor."""
    while True:
        execute(stat)
        time.sleep(120)


def check_complete(jobname_synthax=""):
    """Return true if the user has no job running containing
    jobname_synthax in their name"""
    return jobname_synthax not in stat()


@task
def wait_complete(jobname_synthax):
    """Wait until jobs currently running containing jobname_synthax in
    their name are complete, then return"""
    # time.sleep(120)
    while not check_complete(jobname_synthax):
        time.sleep(120)
