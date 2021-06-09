from fabsim.deploy.templates import *
from fabsim.deploy.machines import *
from fabric.contrib.project import *
from fabric.api import hide, local, run
import time


@task
def stat(jobID=None):
    '''
    Check the remote message queue status for individual machines.
    Syntax: fab <machine> stat.

    TODO: Respect varying remote machine queue systems.
    '''
    check_jobs_dispatched_on_remote_machine()
    jobsInfo = jobs_list(quiet=True)
    print('\n'.join(jobsInfo))


def jobs_list(quiet=False):
    """
        options:
                quiet = True : hide the command output
    """
    if (
            hasattr(env, 'dispatch_jobs_on_localhost') and
            isinstance(env.dispatch_jobs_on_localhost, bool) and
            env.dispatch_jobs_on_localhost
    ):

        output = local(template("$stat "), capture=quiet).splitlines()

    elif env.manual_sshpass:
        pre_cmd = "sshpass -p '%(sshpass)s' ssh %(user)s@%(host)s " % env
        manual_command = template("$stat")
        output = local(pre_cmd + "'" + manual_command + "'", capture=False)

    else:
        with hide("output"):
            output = run(template("$stat"), shell=False).splitlines()

    return output


@task
def cancel_job(jobID=None):
    """
        Cancel a remote job.
        Syntax: fab <machine> cancel_job:jobID

        note : if the jobID is empty, this function cancel all submitted
               job which are not in FINISHED status
    """

    check_jobs_dispatched_on_remote_machine()

    if jobID is None:
        print("ERROR: No jobID is passed,\n\tusage Syntax :"
              "\n\t\tfab <machine> cancel_job:jobID= <input_jobID>")
        sys.exit()

    env.jobID = jobID

    if (
            hasattr(env, "dispatch_jobs_on_localhost") and
            isinstance(env.dispatch_jobs_on_localhost, bool) and
            env.dispatch_jobs_on_localhost
    ):
        return local(template("$cancel_job_command $jobID"))
    elif env.manual_sshpass:
        pre_cmd = "sshpass -p '%(sshpass)s' ssh %(user)s@%(host)s " % env
        manual_command = template("$cancel_job_command $jobID")
        return local(pre_cmd + "'" + manual_command + "'", capture=False)

    else:
        return run(template("$cancel_job_command $jobID"))


def check_jobs_dispatched_on_remote_machine():
    if env.remote == "localhost":
        print("ERROR: This functionality can be used only when"
              "jobs are submitted on the remote machine")
        sys.exit()


def check_complete(jobname_syntax=""):
    """
    Return true if the user has no job running containing
    jobname_syntax in their name
    """
    time.sleep(10)

    check_jobs_dispatched_on_remote_machine()
    jobs_dict = jobs_list(quiet=True)

    if len(jobs_dict) > 0:
        print("The number of active (not finished) jobs = {}".format(
            len(jobs_dict))
        )
        return False
    else:
        print("All jobs are finished :)")
        return True


@task
def wait_complete(jobname_syntax=""):
    """
    Wait until jobs currently running containing jobname_syntax in
    their name are complete, then return
    """
    # time.sleep(120)
    while not check_complete(jobname_syntax):
        time.sleep(110)
