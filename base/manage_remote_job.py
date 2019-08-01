from deploy.templates import *
from deploy.machines import *
from fabric.contrib.project import *
import time


@task
def stat(jobID=None):
    """Check the remote message queue status for individual machines.
    Syntax: fab <machine> stat."""

    return job_stat(jobID)

    # TODO: Respect varying remote machine queue systems.
    # return run(template("$stat -u $username $stat_postfix"))


@task
def job_stat(period="localDB", jobID=None):
    """
        return a report for all submitted jobs or for a specific one
        when using QCG.
        Syntax:
                fab <machine> job_stat

        default :
                reports the status of jobs saved in the local DataBase
                by fetching the results of each job,
                the location of local database is set by $local_jobsDB_path at
                /deploy/machines.yaml file
        options:
                period=all : return task information for all submitted jobs,
                                syntax : fab <machine> job_stat:period=all

                jobID : return the status for a specific task,
                                syntax : fab <machine> job_stat:jobID=...
    """
    # TODO: Respect varying remote machine queue systems.
    # it return the information for all submitted jobs

    check_jobs_dispatched_on_remote_machine()

    jobsInfo = jobs_list(quiet=True, jobsID=jobID)

    if len(jobsInfo) == 0:
        if jobID is not None:
            print('No job found with this configuration -> jobID=%s' % (jobID))
        else:
            print('There is no submitted job by the user yet')
        return

    if period != "localDB" or jobID is not None:
        print_job_info(jobsInfo)
    else:
        jobsID = read_submitted_jobsID()
        print_job_info(dict((key, value)
                            for key, value in jobsInfo.items()
                            if key in jobsID.keys()))

    return jobsInfo


@task
def job_stat_update():
    """
        - Reports on the status of all submitted jobs from the local machine
            (jobIDs are taken from the local database file)
        - also, it updates the job status in the local database file
        Syntax:
                fab <machine> job_stat_update
    """

    check_jobs_dispatched_on_remote_machine()

    check_local_database_file_exist()

    submitted_jobsID = read_submitted_jobsID()
    jobsInfo = jobs_list(quiet=True)

    print("\n%-30s \t %-20s \t %-20s" %
          ("JobID", "current Status", "New Status"))
    print('-' * 30 + " \t " + '-' * 20 + " \t " + '-' * 20)

    for key, value in submitted_jobsID.items():
        if key in jobsInfo:
            JobID = key
            curr_status = value['status']
            new_status = jobsInfo[JobID]['status']

            if (new_status != curr_status):
                update_submitted_job_info(jobID=JobID, status=new_status)
                print("%-30s \t %-20s \t %-20s" %
                      (JobID, curr_status, new_status))
            else:
                print("%-30s \t %-20s \t %-20s" % (JobID, curr_status, '-'))

    return jobsInfo


@task
def job_info(jobID=None):
    """
        return the status of a submitted job.
        Syntax: fab <machine> job_info:jobID
    """

    check_jobs_dispatched_on_remote_machine()

    if jobID is None:
        print("ERROR: No jobID is passed, usage Syntax : \
            fab <machine> job_info:jobID= <input_jobID>")
        sys.exit()

    env.jobID = jobID

    if (
            hasattr(env, 'dispatch_jobs_on_localhost') and
            isinstance(env.dispatch_jobs_on_localhost, bool) and
            env.dispatch_jobs_on_localhost
    ):
        local(template(env.job_info_command))
    else:
        run(template(env.job_info_command))


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


@task
def delete_job(jobID=None, status=None):
    """
        this function delete a job/jobs from local machine,
        one of these parameters (jobID OR status) should be set
        Syntax:
                - fab <machine> delete_job:jobID="...",status="..."

        TODO : should I call it from fetch_results ???
    """

    check_jobs_dispatched_on_remote_machine()

    if jobID is None and status is None:
        print("ERROR: For delete command : one of these parameters "
              "(jobID OR status) should be set\n\tSyntax:"
              "\n\t\tfab <machine> delete_job:jobID='...',status='...'")
        sys.exit()

    check_local_database_file_exist()

    submitted_jobsID = read_submitted_jobsID()

    deleted_jobsID = []
    for key, value in submitted_jobsID.items():
        if (jobID is None or (jobID is not None and key == jobID)) \
            and \
            (status is None or (
                status is not None and status == value['status'])
             ):
            deleted_jobsID.append(key)

    if len(deleted_jobsID) > 0:
        delete_submitted_job_info(deleted_jobsID)
        print("%d jobs are deleted from local DataBase" %
              (len(deleted_jobsID)))
    else:
        print("NO job found with this conditions to be deleted !!!")


def jobs_list(quiet=False, jobsID=None):
    """
        options:
                quiet = True : hide the command output
    """
    # output = local(template("$stat "), capture=quiet)
    if (
            hasattr(env, 'dispatch_jobs_on_localhost') and
            isinstance(env.dispatch_jobs_on_localhost, bool) and
            env.dispatch_jobs_on_localhost
    ):
        output = local(template("$stat "), capture=quiet)
    else:
        output = run(template("$stat"))

    jobsInfo = {}
    for line in output.split('\n'):
        line_parts = line.split()
        JobID, status, host = [line_parts[i] if i < len(
            line_parts) else None for i in range(3)]
        if jobsID is None or JobID in jobsID:
            jobsInfo[JobID] = dict(status=status, host=host)

    return jobsInfo


def save_submitted_job_info():
    """
        this function save the jobID for the just-submitted task
    """

    # 1) checks if the local_jobsDB_path folder is exists (creates it if NOT)
    if not os.path.isdir(env.local_jobsDB_path):
        try:
            os.makedirs(env.local_jobsDB_path)
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    # 2) checks if $env.local_jobsDB_filename file is exist (creates it if NOT)
    # by default, local_jobsDB_filename = jobsDB.txt, you can change it in
    # your local machine configuration file (i.e., machines.yml)
    if not os.path.isfile(os.path.join
                          (env.local_jobsDB_path, env.local_jobsDB_filename)
                          ):
        f = open(os.path.join(env.local_jobsDB_path,
                              env.local_jobsDB_filename), "w")
    else:
        f = open(os.path.join(env.local_jobsDB_path,
                              env.local_jobsDB_filename), "a")

    # 3) retrieves jobID for the last submitted job on the remote machine
    jobsInfo = jobs_list(quiet=True)
    lastTask = {list(jobsInfo.keys())[-1]: jobsInfo[list(jobsInfo.keys())[-1]]}
    JobID = list(lastTask.keys())[0]
    status = lastTask[JobID]['status']
    host = lastTask[JobID]['host']

    # 4) add the jobID into local_jobsDB_filename
    f.write("%-30s \t %-15s \t %-15s\n" % (JobID, status, host))
    f.close()


def read_submitted_jobsID(output_format='dict'):
    """
        this function reads submitted jobIDs for local database,
        returns (only jobIDs) as a dictionary/an array object
    """
    check_local_database_file_exist()

    if output_format != 'dict':
        return open(os.path.join(
            env.local_jobsDB_path,
            env.local_jobsDB_filename), 'r').readlines()

    submitted_jobsID = {}
    with open(os.path.join(
            env.local_jobsDB_path,
            env.local_jobsDB_filename)) as f:
        for line in f:
            line_parts = line.split()
            JobID, status, host = [line_parts[i] if i < len(
                line_parts) else None for i in range(3)]
            submitted_jobsID[JobID] = dict(status=status, host=host)

    return submitted_jobsID


def delete_submitted_job_info(jobID=None):
    """
        this function deletes a jobIDs from local database file
        [check with Derek] other possible solutions:
                     1- awk 'NR != 7' inputfile.txt > outputfile.txt
                     2- grep -E "regex" inputfile.txt > outputfile.txt
    """

    if jobID is None:
        print("ERROR: No jobID is passed to be deleted, jobID=None")
        sys.exit()
    elif isinstance(jobID, list) and len(jobID) == 0:
        print("ERROR: No jobID is passed to be deleted, jobID=[]")
        sys.exit()

    check_local_database_file_exist()

    infile = open(
        os.path.join(
            env.local_jobsDB_path,
            env.local_jobsDB_filename),
        'r').readlines()

    with open(os.path.join(
            env.local_jobsDB_path,
            env.local_jobsDB_filename), 'w') as outfile:
        for line in infile:
            if isinstance(jobID, str) and line.split()[0] != jobID:
                outfile.write(line)
            elif isinstance(jobID, list) and line.split()[0] not in jobID:
                outfile.write(line)


def update_submitted_job_info(jobID=None, status=None):
    """
        this function updates the job's status at local database file
        TODO : add an individual function to read line structure from file !!!
    """

    if jobID is None:
        print("ERROR: No jobID is passed to be updated")
        sys.exit()

    if status is None:
        print("ERROR: No status is passed to be updated")
        sys.exit()

    check_local_database_file_exist()

    infile = open(
        os.path.join(
            env.local_jobsDB_path,
            env.local_jobsDB_filename),
        'r').readlines()

    for idx, line in enumerate(infile):
        """
        line_parts = line.split()
        JobID, old_status, host = [line_parts[i] if i < len(
            line_parts) else None for i in range(3)]
        """
        if line.split()[0] == jobID:
            host = line.split()[2] if len(line.split()) > 2 else ""
            # infile[idx] = "%-30s \t %-15s \t %-15s\n" % (jobID, status, host)
            infile[idx] = "{:30s} \t {:15s} \t {:15s}\n".format(
                jobID, status, host)

    with open(os.path.join(
            env.local_jobsDB_path,
            env.local_jobsDB_filename), 'w') as outfile:
        outfile.writelines(infile)


def check_local_database_file_exist():

    if not os.path.isfile(os.path.join(
            env.local_jobsDB_path, env.local_jobsDB_filename)):
        print("ERROR: The local database file : %s appears not to exist" %
              (os.path.join(env.local_jobsDB_path, env.local_jobsDB_filename)))
        sys.exit()


def check_jobs_dispatched_on_remote_machine():
    if env.remote == 'localhost':
        print("ERROR: This functionality can be used only when\
            jobs are submitted on the remote machine")
        sys.exit()


@task
def monitor():
    """Report on the queue status, ctrl-C to interrupt.
    Syntax: fab <machine> monitor."""
    while True:
        execute(stat)
        time.sleep(120)


def check_complete(jobname_syntax=""):
    """Return true if the user has no job running containing
    jobname_syntax in their name"""

    jobs_dict = stat()
    for key, value in jobs_dict.items():
        if jobname_syntax in key:
            if value['status'] not in ["COMPLETED", "FAILED", "CANCELLED"]:
                print("Still running: ", key, value)
                return False
    return True


@task
def wait_complete(jobname_syntax):
    """Wait until jobs currently running containing jobname_syntax in
    their name are complete, then return"""
    # time.sleep(120)
    while not check_complete(jobname_syntax):
        time.sleep(120)


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
