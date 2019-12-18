from deploy.templates import *
from deploy.machines import *
from fabric.contrib.project import *
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

    print_job_info(jobsInfo)


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
        output = local(template("$stat "), capture=quiet)
    else:
        with hide('output'):
            output = run(template("$stat"))

    jobsInfo = {}
    for line in output.split('\n'):
        line_parts = line.split()
        JobID, status, host = [line_parts[i] if i < len(
            line_parts) else None for i in range(3)]

        if (
            status is None or
            status.lower() not in list(map(str.lower, env.unfinishedJobTags +
                                           env.finishedJobTags))
        ):
            continue

        jobsInfo[JobID] = dict(status=status, host=host)

    return jobsInfo


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
            hasattr(env, 'dispatch_jobs_on_localhost') and
            isinstance(env.dispatch_jobs_on_localhost, bool) and
            env.dispatch_jobs_on_localhost
    ):
        return local(template("$cancel_job_command $jobID"))
    else:
        return run(template("$cancel_job_command $jobID"))


def check_jobs_dispatched_on_remote_machine():
    if env.remote == 'localhost':
        print("ERROR: This functionality can be used only when\
            jobs are submitted on the remote machine")
        sys.exit()


def check_complete(jobname_syntax=""):
    """
    Return true if the user has no job running containing
    jobname_syntax in their name
    """
    time.sleep(10)

    check_jobs_dispatched_on_remote_machine()
    jobs_dict = jobs_list(quiet=True)

    for key, value in jobs_dict.items():
        if jobname_syntax in key:
            if value['status'] not in env.finishedJobTags:
                print("Still running: ", key, value)
                return False
    return True


@task
def wait_complete(jobname_syntax):
    """
    Wait until jobs currently running containing jobname_syntax in
    their name are complete, then return"""
    # time.sleep(120)
    while not check_complete(jobname_syntax):
        time.sleep(110)


def print_job_info(jobs_dict):

    print('\n')
    print("%-30s \t %-15s \t %-15s" % ("JobID", "Job Status", "Host"))
    print('-' * 30 + " \t " + '-' * 15 + " \t " + '-' * 15)

    for key, value in jobs_dict.items():
        JobID = key
        status = value['status']
        host = value['host']
        print("%-30s \t %-15s \t %-15s" % (JobID, status, host))

    print('\n')
