# -*- coding: utf-8 -*-
#
#
# This source file is part of the FabSim software toolkit, which is
# distributed under the BSD 3-Clause license.
# Please refer to LICENSE for detailed information regarding the
# licensing.
#
# fab.py contains general-purpose FabSim routines.
# from base.MultiThreadingPool import MultiThreadingPool
from base.MultiProcessingPool import MultiProcessingPool
from fabric.state import output
from deploy.templates import *
from deploy.machines import *
from fabric.contrib.project import *
from base.manage_remote_job import *
from base.setup_fabsim import *
from fabric.api import settings
import time
import re
import numpy as np
import yaml
import tempfile
import os.path
import math
from pprint import PrettyPrinter, pformat
from pathlib import Path
from shutil import copyfile, rmtree, copy
from fabric.contrib.files import exists

pp = PrettyPrinter()


def get_plugin_path(name, quiet=False):
    """
    Get the local base path of plugin <name>.
    """
    plugin_path = os.path.join(env.localroot, 'plugins', name)

    if not quiet:
        assert os.path.isdir(plugin_path), \
            "The requested plugin %s does not exist (%s).\n \
            you can install it by typing:\n\t \
            fabsim localhost install_plugin:%s" % (name, plugin_path, name)
    return plugin_path


def local_with_stdout(cmd, verbose=False):
    """
    Runs Fabric's local() function, while capturing and returning stdout
    automatically.
    """
    with settings(warn_only=True):
        output = local(cmd, capture=True)
        if verbose:
            print("stdout: %s" % output.stdout)
            print("stderr: %s" % output.stderr)
        return output.stdout


def with_template_job(ensemble_mode=False, label=None):
    """
    Determine a generated job name from environment parameters,
    and then define additional environment parameters based on it.
    """

    # The name is now depending of the label name
    name = template(env.job_name_template)
    if label and not ensemble_mode:
        name = '_'.join((label, name))

    job_results, job_results_local = with_job(name=name,
                                              ensemble_mode=ensemble_mode,
                                              label=label
                                              )

    return job_results, job_results_local


def with_job(name, ensemble_mode=False, label=None):
    """Augment the fabric environment with information regarding a
    particular job name.

    Definitions created:
    job_results: the remote location where job results should be stored
    job_results_local: the local location where job results should be
      stored
    """
    env.name = name
    if not ensemble_mode:
        job_results = env.pather.join(env.results_path, name)
        job_results_local = os.path.join(env.local_results, name)
    else:
        job_results = "%s/RUNS/%s" % (env.pather.join(
            env.results_path, name), label)
        job_results_local = "%s/RUNS/%s" % (os.path.join(
            env.local_results, name), label)

    env.job_results_contents = env.pather.join(job_results, '*')
    env.job_results_contents_local = os.path.join(job_results_local, '*')

    # Template name is now depending of the label of the job when needed
    if label is not None:
        env.job_name_template_sh = "%s_%s.sh" % (name, label)
    else:
        env.job_name_template_sh = "%s.sh" % (name)

    return job_results, job_results_local


def with_template_config():
    """
    Determine the name of a used or generated config from environment
    parameters, and then define additional environment parameters based
    on it.
    """
    with_config(template(env.config_name_template))


def find_config_file_path(name, ExceptWhenNotFound=True):

    # Prevent of executing localhost runs on the FabSim3 root directory
    if env.host == 'localhost' and env.work_path == env.localroot:
        print("Error : the localhost run dir is same as your FabSim3 folder")
        print("To avoid any conflict of config folder, please consider")
        print("changing your home_path_template variable")
        print("you can easily modify it by updating localhost entry in")
        print("your FabSim3/machines_user.yml file")
        print("Here is the suggested changes ")
        print("\nlocalhost:")
        print("  ...")
        print("  home_path_template: \"%s/localhost_exe\"\n"
              % (env.localroot))
        exit()

    path_used = None
    for p in env.local_config_file_path:
        config_file_path = os.path.join(p, name)
        if os.path.exists(config_file_path):
            path_used = config_file_path

    if path_used is None:
        if ExceptWhenNotFound:
            raise Exception(
                "Error: config file directory not found in: ",
                env.local_config_file_path)
        else:
            return False
    return path_used


def with_config(name):
    """
    Internal: augment the fabric environment with information
      regarding a particular configuration name.
    Definitions created:
    job_config_path: the remote location where the config files
      for the job should be stored
    job_config_path_local: the local location where the config files
      for the job may be found
    """
    env.config = name
    env.job_config_path = env.pather.join(env.config_path, name + env.job_desc)

    path_used = find_config_file_path(name)

    env.job_config_path_local = os.path.join(path_used)
    env.job_config_contents = env.pather.join(env.job_config_path, '*')
    env.job_config_contents_local = os.path.join(
        env.job_config_path_local, '*')
    # name of the job sh submission script.
    env.job_name_template_sh = template("%s.sh" % env.job_name_template)


def with_profile(name):
    """
    Internal: augment the fabric environment with information
    regarding a particular profile name

    Definitions created:
    job_profile_path: the remote location where the profile should be
      stored
    job_profile_path_local: the local location where the profile files
      may be
    found
    """
    env.profile = name
    env.job_profile_path = env.pather.join(
        env.profiles_path, name)
    env.job_profile_path_local = os.path.join(
        env.local_profiles, name)
    env.job_profile_contents = env.pather.join(
        env.job_profile_path, '*')
    env.job_profile_contents_local = os.path.join(
        env.job_profile_path_local, '*')


@task
def fetch_configs(config=''):
    """
    Fetch config files from the remote, via rsync. Specify a config
    directory, such as 'cylinder' to copy just one config. Config files
    are stored as, e.g. cylinder/config.dat and cylinder/config.xml
    Local path to use is specified in machines_user.json, and should
    normally point to a mount on entropy, i.e.
    /store4/blood/username/config_files
    This method is not intended for normal use, but is useful when the
    local machine cannot have an entropy mount, so that files can be
    copied to a local machine from entropy, and then transferred to the
    compute machine, via 'fab entropy fetch_configs; fab legion
    put_configs'
    """
    with_config(config)
    if env.manual_gsissh:
        local(
            template(
                "globus-url-copy -cd -r -sync \
                gsiftp://$remote/$job_config_path/ \
                file://$job_config_path_local/"
            )
        )
    else:
        local(
            template(
                "rsync -pthrvz $username@$remote:$job_config_path/ \
                $job_config_path_local"
            )
        )


@task
def put_configs(config=''):
    """
    Transfer config files to the remote. For use in launching jobs, via
    rsync. Specify a config directory, such as 'cylinder' to copy just
    one configuration. Config files are stored as, e.g. cylinder/config.dat
    and cylinder/config.xml Local path to find config directories is
    specified in machines_user.json, and should normally point to a mount
    on entropy, i.e. /store4/blood/username/config_files If you can't mount
    entropy, 'fetch_configs' can be useful, via 'fab entropy fetch_configs;
    fab legion put_configs'

    RECENT ADDITION: Added get_setup_fabsim_dirs_string() so that the
    Fabric Directories are now created automatically whenever
    a config file is uploaded.
    """

    with_config(config)
    run(
        template(
            "%s; mkdir -p $job_config_path" % (get_setup_fabsim_dirs_string())
        )
    )

    rsync_delete = False
    if (hasattr(env, 'prevent_results_overwrite') and
            env.prevent_results_overwrite == 'delete'):
        rsync_delete = True

    if env.manual_sshpass:
        # TODO: maybe the better option here is to overwrite the rsync_project
        # function from /fabric/contrib/project.py
        local(
            template(
                "rsync -pthrvz --rsh='sshpass -p $sshpass ssh  -p 22  ' \
                $job_config_path_local/ \
                $username@$remote:$job_config_path/ "
            )
        )
    elif env.manual_gsissh:
        # TODO: implement prevent_results_overwrite here
        local(
            template(
                "globus-url-copy -p 10 -cd -r -sync \
                file://$job_config_path_local/ \
                gsiftp://$remote/$job_config_path/"
            )
        )
    else:
        rsync_project(
            local_dir=env.job_config_path_local + '/',
            remote_dir=env.job_config_path,
            delete=rsync_delete
        )


@task
def put_results(name=''):
    """
    Transfer result files to a remote. Local path to find result
    directories is specified in machines_user.json. This method is not
    intended for normal use, but is useful when the local machine
    cannot have an entropy mount, so that results from a local machine
    can be sent to entropy, via 'fab legion fetch_results; fab entropy
    put_results'
    """
    with_job(name)
    run(template("mkdir -p $job_results"))
    if env.manual_gsissh:
        local(
            template(
                "globus-url-copy -p 10 -cd -r -sync \
                file://$job_results_local/ \
                gsiftp://$remote/$job_results/"))
    else:
        rsync_project(
            local_dir=env.job_results_local + '/',
            remote_dir=env.job_results
        )


@task
def fetch_results(name='', regex='', debug=False):
    """
    Fetch results of remote jobs to local result store. Specify a job
    name to transfer just one job. Local path to store results is
    specified in machines_user.json, and should normally point to a
    mount on entropy, i.e. /store4/blood/username/results.
    If you can't mount entropy, 'put results' can be useful, via
    'fab legion fetch_results; fab entropy put_results'
    """

    if debug:
        pp.pprint(env)
    env.job_results, env.job_results_local = with_job(name)
    if env.manual_sshpass:
        local(
            template(
                "rsync -pthrvz -e 'sshpass -p $sshpass ssh -p $port' \
                $username@$remote:$job_results/%s \
                $job_results_local" % regex
            )
        )
    elif env.manual_gsissh:
        local(
            template(
                "globus-url-copy -cd -r -sync \
                gsiftp://$remote/$job_results/%s \
                file://$job_results_local/" % regex
            )
        )
    else:
        local(
            template(
                # "rsync -pthrvz --port=$port \
                "rsync -pthrvz -e 'ssh -p $port' \
                $username@$remote:$job_results/%s \
                $job_results_local" % regex
            )
        )


@task
def clear_results(name=''):
    """Completely wipe all result files from the remote."""
    with_job(name)
    run(template('rm -rf $job_results_contents'))


@task
def fetch_profiles(name=''):
    """
    Fetch results of remote jobs to local result store. Specify a job
    name to transfer just one job. Local path to store results is
    specified in machines_user.json, and should normally point to a
    mount on entropy, i.e. /store4/blood/username/results.
    If you can't mount entropy, 'put results' can be useful, via
    'fab legion fetch_results; fab entropy put_results'
    """
    with_profile(name)
    if env.manual_gsissh:
        local(
            template(
                "globus-url-copy -cd -r -sync \
                gsiftp://$remote/$job_profile_path/ \
                file://$job_profile_path_local/"
            )
        )
    else:
        local(
            template(
                "rsync -pthrvz $username@$remote:$job_profile_path/ \
                $job_profile_path_local"
            )
        )


@task
def put_profiles(name=''):
    """
    Transfer result files to a remote. Local path to find result
    directories is specified in machines_user.json. This method is not
    intended for normal use, but is useful when the local machine
    cannot have an entropy mount, so that results from a local machine
    can be sent to entropy, via 'fab legion fetch_results;
    fab entropy put_results'
    """
    with_profile(name)
    run(template("mkdir -p $job_profile_path"))
    if env.manual_gsissh:
        local(
            template("globus-url-copy -p 10 -cd -r -sync \
            file://$job_profile_path_local/ \
            gsiftp://$remote/$job_profile_path/")
        )
    else:
        rsync_project(
            local_dir=env.job_profile_path_local + '/',
            remote_dir=env.job_profile_path
        )

    """
    Returns the commands required to set up the fabric directories. This
    is not in the env, because modifying this is likely to break FabSim
    in most cases. This is stored in an individual function, so that the
    string can be appended in existing commands, reducing the
    performance overhead.
    """
    return(
        'mkdir -p $config_path; mkdir -p $results_path; mkdir -p $scripts_path'
    )


def update_environment(*dicts):
    for adict in dicts:
        env.update(adict)


def calc_nodes():
    # If we're not reserving whole nodes, then if we request less than one
    # node's worth of cores, need to keep N<=n
    env.coresusedpernode = env.corespernode
    if int(env.coresusedpernode) > int(env.cores):
        env.coresusedpernode = env.cores
    env.nodes = int(math.ceil(float(env.cores) / float(env.coresusedpernode)))


def calc_total_mem():
    # for qcg scheduler, #QCG memory requires total memory for all nodes
    if not hasattr(env, 'memory'):
        env.memory = '2GB'

    mem_size = int(re.findall("\d+", str(env.memory))[0])
    try:
        mem_unit_str = re.findall("[a-zA-Z]+", str(env.memory))[0]
    except Exception:
        mem_unit_str = ''

    if mem_unit_str.upper() == 'GB' or mem_unit_str.upper() == 'G':
        mem_unit = 1000
    else:
        mem_unit = 1

    if(hasattr(env, 'PJ') and env.PJ.lower() == 'true'):
        # env.total_mem = mem_size * int(env.PJ_size) * mem_unit
        env.total_mem = env.memory
    else:
        env.total_mem = mem_size * int(env.nodes) * mem_unit


@task
def get_fabsim_git_hash(verbose=True):
    with settings(warn_only=True):
        return local_with_stdout("git rev-parse HEAD", verbose=True)


@task
def get_fabsim_command_history():
    """
    Parses the bash history, and returns all the instances that contain
    the phrase "fab ".
    """
    return local_with_stdout(
        "cat %s/.bash_history | grep fab" % (env.localhome), verbose=True
    )


def removekey(d, key):
    r = dict(d)
    try:
        del r[key]
    except KeyError as ex:
        pass
    return r


def job(*job_args):
    """
    Internal low level job launcher.
    Parameters for the job are determined from the prepared fabric environment
    Execute a generic job on the remote machine.

    To improve the total job submission, and reduce the number of SSH
    connection for job files/folders transmission, the job submission workflow
    splitted into 3 individual sub-workflow
                                1) job_preparation
                                2) job_transmission
                                3) job_submission

    Returns the generate jobs scripts for submission on the remote machine.
    """

    args = {}
    for adict in job_args:
        args = dict(args, **adict)

    # check if with_config function is already called or not
    if not hasattr(env, 'job_config_path'):
        raise RuntimeError('Function with_config did NOT called, '
                           'Please call it before calling job()')
        # sys.exit()

    update_environment(args)
    #   Add label, mem, core to env.
    calc_nodes()
    calc_total_mem()

    if 'sweepdir_items' in args:
        env.ensemble_mode = True
    else:
        env.ensemble_mode = False

    ########################################################
    #  temporary folder to save job files/folders/scripts  #
    ########################################################
    env.tmp_work_path = env.pather.join(
        tempfile._get_default_tempdir(),
        next(tempfile._get_candidate_names()),
        'FabSim3'
        # env.fabric_dir
    )

    if os.path.exists(env.tmp_work_path):
        rmtree(env.tmp_work_path)
    # the config_files folder is already transfered by put_config
    env.tmp_results_path = env.pather.join(env.tmp_work_path, 'results')
    env.tmp_scripts_path = env.pather.join(env.tmp_work_path, 'scripts')
    os.makedirs(env.tmp_scripts_path)
    os.makedirs(env.tmp_results_path)

    POOL = MultiProcessingPool(PoolSize=int(env.nb_process))

    #####################################
    #       job preparation phase       #
    #####################################
    print_msg_box(title="job preparation phase",
                  msg='tmp_work_path = %s ' % (env.tmp_work_path)
                  )

    print("Submit tasks to multiprocessingPool : start ...")
    if env.ensemble_mode is True:
        for task_label in env.sweepdir_items:
            POOL.add_task(
                func=job_preparation,
                func_args=dict(ensemble_mode=env.ensemble_mode,
                               label=task_label)
            )
    else:
        POOL.add_task(
            func=job_preparation,
            func_args=args
        )

    print("Submit tasks to multiprocessingPool : done ...")
    job_scripts_to_submit = POOL.wait_for_tasks()

    #####################################
    #       job transmission phase      #
    #####################################
    print_msg_box(title="job transmission phase",
                  msg='Copy all generated files/folder from\n'
                  'tmp_work_path = %s\n'
                  'to\n'
                  'work_path = %s' % (env.tmp_work_path, env.work_path)
                  )

    job_transmission()

    if not (hasattr(env, 'TestOnly') and env.TestOnly.lower() == 'true'):
        # DO NOT submit any job
        # env.submit_job is False in case of using PilotJob option
        # therefore, DO NOT submit the job directly, only submit PJ script
        if not (hasattr(env, 'submit_job') and
                isinstance(env.submit_job, bool) and
                env.submit_job is False):
            #####################################
            #       job submission phase      #
            #####################################
            print_msg_box(title="job submission phase",
                          msg="Submit all generated job scripts to"
                          " the target remote machine"
                          )

            for job_script in job_scripts_to_submit:
                job_submission(dict(job_script=job_script))
            print("submitted job script = \n{}".format(
                pformat(job_scripts_to_submit))
            )

    # POOL.shutdown_threads()

    return job_scripts_to_submit


def job_submission(*job_args):
    """
    here, all prepared job scrips will be submitted to the
    target remote machine

    Note:
            - please make sure to pass the list of job scripts be summited as
              an input to this function
    """

    args = {}
    for adict in job_args:
        args = dict(args, **adict)

    job_script = args['job_script']

    if hasattr(env, 'dispatch_jobs_on_localhost') and \
            isinstance(env.dispatch_jobs_on_localhost, bool) and \
            env.dispatch_jobs_on_localhost:
        local(template("$job_dispatch " + job_script))
        print("job dispatch is done locally\n")

    elif not env.get("noexec", False):
        if env.remote == 'localhost':
            with cd(env.pather.dirname(job_script)):
                with prefix(env.run_prefix):
                    # print(template("\n\n$job_dispatch %s\n\n" % job_script))
                    run(template("$job_dispatch %s" % job_script))
        else:
            with cd(env.pather.dirname(job_script)):
                # print(template("\n\n$job_dispatch %s\n\n" % job_script))
                run(template("$job_dispatch %s" % job_script))

    print("Use `fab %s fetch_results` to copy the results "
          "back to localhost." % (env.machine_name)
          )

    return [job_script]


def job_transmission(*job_args):
    """
    here, we only transfer all generated files/folders from
        <tmp_folder>/{results,scripts}
    to
        <target_work_dir>/{results,scripts}
    """
    args = {}
    for adict in job_args:
        args = dict(args, **adict)

    if (hasattr(env, 'prevent_results_overwrite') and
            env.prevent_results_overwrite == 'delete'):
        # if we have a large result directory contains thousands of files and
        # folders, using rm command will not be efficient,
        # so, here I am using rsync
        #
        # Note: there is another option, using perl which is much faster than
        #       rsync -a --delete, but I am not sure if we can use it on
        #       all HPC resources
        empty_folder = "/tmp/{}".format(next(tempfile._get_candidate_names()))
        results_dir_items = os.listdir(env.tmp_results_path)
        for results_dir_item in results_dir_items:
            run(template("mkdir %s && "
                         "mkdir -p %s/results &&"
                         "rsync -a --delete %s/  %s/results/%s/"
                         % (
                             empty_folder, env.work_path,
                             empty_folder, env.work_path, results_dir_item)
                         ))

    rsyc_src_dst_folders = []
    rsyc_src_dst_folders.append((env.tmp_scripts_path, env.scripts_path))
    rsyc_src_dst_folders.append((env.tmp_results_path, env.results_path))

    for sync_src, sync_dst in rsyc_src_dst_folders:
        if env.manual_sshpass:
            # TODO: maybe the better option here is to overwrite the
            #       rsync_project
            local(
                template("rsync -pthrvz \
                    --rsh='sshpass -p $sshpass ssh  -p 22  ' \
                    %s/ $username@$remote:%s/ " % (sync_src, sync_dst)
                         )
            )
        elif env.manual_gsissh:
            # TODO: implement prevent_results_overwrite for this option
            local(
                template(
                    "globus-url-copy -p 10 -cd -r -sync \
                    file://%s/ \
                    gsiftp://$remote/%s/" % (sync_src, sync_dst)
                )
            )
        else:
            rsync_project(
                local_dir=sync_src + '/',
                remote_dir=sync_dst
            )


def job_preparation(*job_args):
    """
    here, all job folders and scripts will be created in the temporary folder
        <tmp_folder>/{results,scripts}
    later, in job_transmission, we transfer all these files and folders with
    a single rsync command.
    This approach will helps us to reduce the number of SSH connection and
    improve the stability of job submission workflow which can be compromised
    by high parallel SSH connection
    """

    args = {}
    for adict in job_args:
        args = dict(args, **adict)

    if 'label' in args:
        env.label = args['label']
    else:
        env.label = ''

    return_job_scripts = []
    for i in range(1, int(env.replicas) + 1):

        env.job_results, env.job_results_local = with_template_job(
            ensemble_mode=env.ensemble_mode,
            label=env.label
        )

        if int(env.replicas) > 1:
            if env.ensemble_mode is False:
                env.job_results += '_replica_' + str(i)
            else:
                env.job_results += '_' + str(i)

        tmp_job_results = env.job_results.replace(env.results_path,
                                                  env.tmp_results_path)

        env['job_name'] = env.name[0:env.max_job_name_chars]
        complete_environment()

        env.run_command = template(env.run_command)

        if env.label not in ['PJ_PYheader', 'PJ_header']:
            env.run_prefix += "\n\n" \
                "# copy files from config folder\n" \
                "config_dir=%s\n" \
                "rsync -pthrvz --exclude SWEEP $config_dir/* ." % (
                    env.job_config_path)

        if env.ensemble_mode:
            env.run_prefix += "\n\n"\
                "# copy files from SWEEP folder\n"\
                "rsync -pthrvz $config_dir/SWEEP/%s/ ." % (
                    env.label
                )

        if not (hasattr(env, 'venv') and env.venv.lower() == 'true'):
            if hasattr(env, 'py_pkg') and len(env.py_pkg) > 0:
                env.run_prefix += "\n\n"\
                    "# Install requested python packages\n"\
                    "pip install --user --upgrade %s" % (
                        ' '.join(pkg for pkg in env.py_pkg)
                    )

        # this is a tricky situation,
        # in case of ensemble runs, or simple job, we need to add env.label
        # to generated job script name,
        # however, for PJ_PYheader and PJ_header header script, nothing should
        # be added at the end of script file name, so, here we pass a empty
        # string as label
        if (hasattr(env, 'NoEnvScript') and env.NoEnvScript):
            tmp_job_script = script_templates(
                env.batch_header
            )
        else:
            tmp_job_script = script_templates(
                env.batch_header,
                env.script
            )

        # Separate base from extension
        base, extension = os.path.splitext(env.pather.basename(tmp_job_script))
        # Initial new name if we have replicas or ensemble

        if int(env.replicas) > 1:
            if env.ensemble_mode is False:
                dst_script_name = base + '_replica_' + str(i) + extension
            else:
                dst_script_name = base + '_' + str(i) + extension
        else:
            dst_script_name = base + extension

        dst_job_script = env.pather.join(env.tmp_scripts_path, dst_script_name)

        # Add target job script to return list

        '''
        return_job_scripts.append(env.pather.join(env.scripts_path,
                                               dst_script_name)
        '''
        # here, instead of returning PATH to script folder, it is better to
        # submit script from results_path folder, specially in case of PJ job
        return_job_scripts.append(env.pather.join(env.job_results,
                                                  dst_script_name)
                                  )

        copy(tmp_job_script, dst_job_script)
        # chmod +x dst_job_script
        os.chmod(dst_job_script, 0o755)

        os.makedirs(tmp_job_results)
        copy(dst_job_script, env.pather.join(tmp_job_results,
                                             dst_script_name))

        # TODO: these env variables are not used anywhere
        # TODO: maybe it is better to remove them
        # job_name_template_sh
        # job_results_contents
        # job_results_contents_local
        with open(env.pather.join(tmp_job_results, 'env.yml'), 'w')\
                as env_yml_file:
            yaml.dump(dict(env, **{"sshpass": None,
                                   "passwords": None,
                                   "password": None,
                                   "sweepdir_items": None}
                           ),
                      env_yml_file,
                      default_flow_style=False
                      )

    return return_job_scripts


@task
def ensemble2campaign(results_dir, campaign_dir, skip=0, **args):
    """
    Converts FabSim3 ensemble results to EasyVVUQ campaign definition.
    results_dir: FabSim3 results root directory
    campaign_dir: EasyVVUQ root campaign directory.
    skip: The number of runs (run_1 to run_skip) not to copy to the campaign
    """
    update_environment(args)
    # if skip > 0: only copy the run directories run_X for X > skip back
    # to the EasyVVUQ campaign dir
    if int(skip) > 0:
        # all run directories
        runs = os.listdir('%s/RUNS/' % results_dir)
        for run in runs:
            # extract X from run_X
            run_id = int(run.split('_')[-1])
            # if X > skip copy results back
            if run_id > int(skip):
                local("rsync -pthrvz %s/RUNS/%s %s/runs" % (results_dir, run,
                                                            campaign_dir))
    # copy all runs from FabSim results directory to campaign directory
    else:
        local("rsync -pthrvz %s/RUNS/ %s/runs" % (results_dir, campaign_dir))


@task
def campaign2ensemble(config, campaign_dir, skip=0, **args):
    """
    Converts an EasyVVUQ campaign run set TO a FabSim3 ensemble definition.
    config: FabSim3 configuration name (will create in top level if
    non-existent, and overwrite existing content).
    campaign_dir: EasyVVUQ root campaign directory.
    skip: The number of runs (run_1 to run_skip) not to copy to the FabSim3
          sweep directory. The first skip number of samples will then not
          be computed.
    """
    update_environment(args)
    config_path = find_config_file_path(config, ExceptWhenNotFound=False)
    if config_path is False:
        local("mkdir -p %s/%s" % (env.local_config_file_path[-1], config))
        config_path = "%s/%s" % (env.local_config_file_path[-1], config)
    sweep_dir = config_path + "/SWEEP"
    local("mkdir -p %s" % (sweep_dir))

    local('rm -rf %s/*' % (sweep_dir))
    '''
    # the previous ensemble in the sweep directory
    prev_runs = os.listdir(sweep_dir)
    # empty sweep directory
    for prev_run in prev_runs:
        local('rm -r %s/%s' % (sweep_dir, prev_run))
    '''

    # if skip > 0: only copy the run directories run_X for X > skip to the
    # FabSim3 sweep directory. This avoids recomputing already computed samples
    # when the EasyVVUQ grid is refined adaptively.
    if int(skip) > 0:
        # all runs in the campaign dir
        runs = os.listdir('%s/runs/' % campaign_dir)

        for run in runs:
            # extract X from run_X
            run_id = int(run.split('_')[-1])
            # if X > skip, copy run directory to the sweep dir
            if run_id > int(skip):
                print("Copying %s" % run)
                local("rsync -pthrz %s/runs/%s %s" % (campaign_dir, run,
                                                      sweep_dir))
    # if skip = 0: copy all runs from EasyVVUQ run directort to the sweep dir
    else:
        local("rsync -pthrz %s/runs/ %s" % (campaign_dir, sweep_dir))


def run_ensemble(config, sweep_dir, sweep_on_remote=False,
                 execute_put_configs=True, **args):
    """
    Map and execute ensemble jobs.
    The job results will be stored with a name pattern as defined in
    the environment,
    e.g. water-abcd1234-legion-256

    config : base config directory to use to define input files,
        e.g. config=water
    sweep_dir : directory containing inputs that will vary per
        ensemble simulation instance.

    These can either be stored as a range of files or as a range of
    subdirectories.
    Keyword arguments:
            input_name_in_config : name of included file once embedded in
                the simulation config.
            cores : number of compute cores to request
            wall_time : wall-time job limit
            memory : memory per node
    """
    update_environment(args)

    if "script" not in env:
        print("ERROR: run_ensemble function has been called,\
               but the parameter 'script' was not specified.")
        sys.exit()

    # check if with_config function is already called or not
    if not hasattr(env, 'job_config_path'):
        raise RuntimeError('Function with_config did NOT called, '
                           'Please call it before calling run_ensemble()')
        # sys.exit()

    # check for PilotJob option
    if(hasattr(env, 'PJ') and env.PJ.lower() == 'true'):
        # env.batch_header = "no_batch"
        env.submitted_jobs_list = []
        env.submit_job = False
        env.batch_header = "bash_header"

    if sweep_on_remote is False:
        sweepdir_items = os.listdir(sweep_dir)
    else:
        # in case of reading SWEEP folder from remote machine, we need a
        # SSH tunnel and then list the directories
        sweepdir_items = run("ls -1 %s" % (sweep_dir)).splitlines()

    if len(sweepdir_items) == 0:
        print(
            "ERROR: no files where found in the sweep_dir of this\
            run_ensemble command."
        )
        print("Sweep dir location: %s" % (sweep_dir))
        sys.exit()

    # reorder an exec_first item for priority execution.
    if(hasattr(env, 'exec_first')):
        sweepdir_items.insert(
            0, sweepdir_items.pop(
                sweepdir_items.index(
                    env.exec_first)))

    if execute_put_configs is True:
        with hide('everything'):
            execute(put_configs, config)

    # output['everything'] = False
    job_scripts_to_submit = job(dict(ensemble_mode=True,
                                     sweepdir_items=sweepdir_items,
                                     sweep_dir=sweep_dir)
                                )

    if (hasattr(env, 'PJ') and env.PJ.lower() == 'true'):
        print_msg_box(msg="NOW, we submit PJ jobs")

        # first, add all generated tasks script to PJ_PY
        submitted_jobs_list = []
        if not hasattr(env, 'task_model'):
            env.task_model = 'default'
        # Python's indexes start at zero, to start from 1, set start=1
        for index, job_script in enumerate(job_scripts_to_submit, start=1):
            # TODO: this loop should be improved
            env.idsID = index
            env.idsPath = job_script
            submitted_jobs_list.append(
                script_template_content('qcg-PJ-task-template')
            )
        env.submitted_jobs_list = "\n".join(submitted_jobs_list)

        # to avoid apply replicas functionality on PilotJob folders
        env.replicas = '1'
        backup_header = env.batch_header
        env.batch_header = env.PJ_PYheader
        job_scripts_to_submit = job(dict(ensemble_mode=False,
                                         label='PJ_PYheader',
                                         NoEnvScript=True)
                                    )

        env.PJ_PATH = job_scripts_to_submit[0]
        env.PJ_FileName = env.pather.basename(env.PJ_PATH)
        env.batch_header = env.PJ_header
        env.submit_job = True
        # load QCG-PJ-PY file
        PJ_CMD = []
        if (hasattr(env, 'venv') and env.venv.lower() == 'true'):
            # QCG-PJ should load from virtualenv
            PJ_CMD.append('# unload any previous loaded python module')
            PJ_CMD.append('module unload python\n')
            PJ_CMD.append('# load QCG-PilotJob from VirtualEnv')
            PJ_CMD.append('eval "$(%s/bin/conda shell.bash hook)"\n' %
                          (env.virtual_env_path))
            PJ_CMD.append('# load QCG-PJ-Python file')
            PJ_CMD.append('%s/bin/python3 %s' % (env.virtual_env_path,
                                                 env.PJ_PATH))

        else:
            PJ_CMD.append('# Install QCG-PJ in user\'s home space')
            PJ_CMD.append('pip3 install --user --upgrade  qcg-pilotjob\n')
            PJ_CMD.append('# load QCG-PJ-Python file')
            PJ_CMD.append('python3 %s' % (env.PJ_PATH))

        env.run_QCG_PilotJob = "\n".join(PJ_CMD)
        job(dict(ensemble_mode=False,
                 label='PJ_header',
                 NoEnvScript=True)
            )
        env.batch_header = backup_header
        env.NoEnvScript = False


def input_to_range(arg, default):
    ttype = type(default)
    # regexp for a array generator like [1.2:3:0.2]
    gen_regexp = r"\[([\d\.]+):([\d\.]+):([\d\.]+)\]"
    if not arg:
        return [default]
    match = re.match(gen_regexp, str(arg))
    if match:
        vals = list(map(ttype, match.groups()))
        if ttype == int:
            return range(*vals)
        else:
            return np.arange(*vals)
    return [ttype(arg)]


@task
def get_running_location(job=None):
    """
    Returns the node name where a given job is running.
    """
    if job:
        with_job(job)
    env.running_node = run(template("cat $job_results/env_details.asc"))


def manual_sshpass(cmd):
    commands = env.command_prefixes[:]
    if env.get('cwd'):
        commands.append("cd %s" % env.cwd)
    commands.append(cmd)
    manual_command = " && ".join(commands)
    if not hasattr(env, "sshpass"):
        raise ValueError("sshpass value did not set for this remote machine")
        sys.exit()
    pre_cmd = "sshpass -p '%(sshpass)s' ssh %(user)s@%(host)s " % env
    local(pre_cmd + "'" + manual_command + "'", capture=True)


def manual(cmd):
    # From the fabric wiki, bypass fabric internal ssh control
    commands = env.command_prefixes[:]
    if env.get('cwd'):
        commands.append("cd %s" % env.cwd)
    commands.append(cmd)
    manual_command = " && ".join(commands)
    pre_cmd = "ssh -Y -p %(port)s %(user)s@%(host)s " % env
    local(pre_cmd + "'" + manual_command + "'", capture=False)


def manual_gsissh(cmd):
    # From the fabric wiki, bypass fabric internal ssh control
    commands = env.command_prefixes[:]
    if env.get('cwd'):
        commands.append("cd %s" % env.cwd)
    commands.append(cmd)
    manual_command = " && ".join(commands)
    pre_cmd = "gsissh -t -p %(port)s %(host)s " % env
    local(pre_cmd + "'" + manual_command + "'", capture=False)


def run(cmd):
    if env.manual_sshpass:
        manual_sshpass(cmd)
    elif env.manual_gsissh:
        manual_gsissh(cmd)
    elif env.manual_ssh:
        manual(cmd)
    else:
        return fabric.api.run(cmd)


def put(src, dest):
    if env.manual_gsissh:
        if os.path.isdir(src):
            if src[-1] != '/':
                env.manual_src = src + '/'
                env.manual_dest = dest + '/'
        else:
            env.manual_src = src
            env.manual_dest = dest
        local(
            template("globus-url-copy -sync -r -cd -p 10\
                file://$manual_src gsiftp://$host/$manual_dest")
        )
    elif env.manual_ssh:
        env.manual_src = src
        env.manual_dest = dest
        local(template("scp $manual_src $user@$host:$manual_dest"))
    else:
        fabric.api.put(src, dest)


@task
def blackbox(script='ibi.sh', args=''):
    """ black-box script execution. """
    for p in env.local_blackbox_path:
        script_file_path = os.path.join(p, script)
        if os.path.exists(os.path.dirname(script_file_path)):
            local("%s %s" % (script_file_path, args))
            return
    print(
        "FabSim Error: could not find blackbox() script file.\
        FabSim looked for it in the following directories: ",
        env.local_blackbox_path)


@task
def probe(label="undefined"):
    """ Scans a remote site for the presence of certain software. """
    return run("module avail 2>&1 | grep %s" % label)


@task
def archive(prefix, archive_location):
    """ Cleans results directories of core dumps and moves results to
    archive locations. """
    if len(prefix) < 1:
        print("error: no prefix defined.")
        sys.exit()
    print("LOCAL %s %s %s*" % (env.local_results, prefix, archive_location))
    local("rm -f %s/*/core" % (env.local_results))
    local("mv -i %s/%s* %s/" % (env.local_results, prefix, archive_location))
    parent_path = os.sep.join(env.results_path.split(os.sep)[:-1])
    print("REMOTE MOVE: mv %s/%s %s/Backup" %
          (env.results_path, prefix, parent_path))
    run("mkdir -p %s/Backup" % (parent_path))
    run("mv -i %s/%s* %s/Backup/" % (env.results_path, prefix, parent_path))


@task
def print_config(args=''):
    """ Prints local environment """
    for x in env:
        print(x, ':', env[x])


@task
def install_packages(venv='False'):
    """
    Install list of packages defined in deploy/applications.yml
    note : if you got an error on your local machine during the build wheel
    for scipy, like this one
        ERROR: lapack_opt_info:
    Try to install BLAS and LAPACK first. by
    sudo apt-get install libblas-dev liblapack-dev libatlas-base-dev gfortran
    """
    applications_yml_file = os.path.join(env.localroot, 'deploy',
                                         'applications.yml')
    user_applications_yml_file = os.path.join(env.localroot, 'deploy',
                                              'applications_user.yml')
    if not os.path.exists(user_applications_yml_file):
        copyfile(applications_yml_file, user_applications_yml_file)

    config = yaml.load(open(user_applications_yml_file),
                       Loader=yaml.SafeLoader
                       )

    tmp_app_dir = "%s/tmp_app" % (env.localroot)
    local('mkdir -p %s' % (tmp_app_dir))

    for dep in config['packages']:
        local('pip3 download --no-binary=:all: -d %s %s' % (tmp_app_dir, dep))
    add_dep_list_compressed = sorted(Path(tmp_app_dir).iterdir(),
                                     key=lambda f: f.stat().st_mtime)
    for it in range(len(add_dep_list_compressed)):
        add_dep_list_compressed[it] = os.path.basename(
            add_dep_list_compressed[it])

    # Create  directory in the remote machine to store dependency packages
    run(
        template(
            "mkdir -p %s" % env.app_repository
        )
    )

    # Send the dependencies (and the dependencies of dependencies) to the
    # remote machine
    for whl in os.listdir(tmp_app_dir):
        local(
            template(
                "rsync -pthrvz -e 'ssh -p $port'  %s/%s \
                $username@$remote:$app_repository" % (tmp_app_dir, whl)
            )
            # "rsync -pthrvz %s/%s eagle:$app_repository"%(tmp_app_dir, whl)
        )

    # Set required env variable
    env.config = "Install_VECMA_App"
    # env.nodes = 1
    env.nodes = env.cores
    script = os.path.join(tmp_app_dir, "script")
    # Write the Install command in a file
    with open(script, "w") as sc:
        install_dir = "--user"
        if venv == 'True':
            sc.write("if [ ! -d %s ]; then \n\t python -m virtualenv \
                    %s || echo 'WARNING : virtualenv is not installed \
                    or has a problem' \nfi\n\nsource %s/bin/activate\n" %
                     (env.virtual_env_path, env.virtual_env_path,
                      env.virtual_env_path))
            install_dir = ""

        # First install the additional_dependencies
        for dep in reversed(add_dep_list_compressed):
            print(dep)
            if dep.endswith('.zip'):
                sc.write("\nunzip %s/%s -d %s && cd %s/%s \
                        && python3 setup.py install %s"
                         % (env.app_repository, dep, env.app_repository,
                            env.app_repository, dep.replace(".zip", ""),
                            install_dir))
            elif dep.endswith('.tar.gz'):
                sc.write("\ntar xf %s/%s -C %s && cd %s/%s \
                        && python3 setup.py install %s\n"
                         % (env.app_repository, dep, env.app_repository,
                            env.app_repository, dep.replace(".tar.gz", ""),
                            install_dir))

    # Add the tmp_app_dir directory in the local templates path because the
    # script is saved in it
    env.local_templates_path.insert(0, tmp_app_dir)

    install_dict = dict(script="script")
    # env.script = "script"
    update_environment(install_dict)

    # Determine a generated job name from environment parameters
    # and then define additional environment parameters based on it.
    env.job_results, env.job_results_local = with_template_job()

    # Create job script based on "sbatch header" and script created above in
    # deploy/.jobscript/
    env.job_script = script_templates(env.batch_header_install_app, env.script)

    # Create script's destination path to remote machine based on
    env.dest_name = env.pather.join(
        env.scripts_path, env.pather.basename(env.job_script)
    )

    # Send Install script to remote machine
    put(env.job_script, env.dest_name)
    #
    run(template("mkdir -p $job_results"))
    with cd(env.pather.dirname(env.job_results)):
        run(template("%s %s") % (env.job_dispatch, env.dest_name))

    local('rm -rf %s' % tmp_app_dir)


@task
def install_app(name="", external_connexion='no', venv='False'):
    """
    Install a specific Application through FasbSim3

    """
    applications_yml_file = os.path.join(env.localroot, 'deploy',
                                         'applications.yml')
    user_applications_yml_file = os.path.join(env.localroot, 'deploy',
                                              'applications_user.yml')
    if not os.path.exists(user_applications_yml_file):
        copyfile(applications_yml_file, user_applications_yml_file)

    config = yaml.load(open(user_applications_yml_file),
                       Loader=yaml.SafeLoader
                       )
    info = config[name]

    # Offline cluster installation - --user install
    # Temporary folder
    tmp_app_dir = "%s/tmp_app" % (env.localroot)
    local('mkdir -p %s' % (tmp_app_dir))

    # First download all the Miniconda3 installation script
    local('wget %s -O %s/miniconda.sh' %
          (config['Miniconda-installer']['repository'], tmp_app_dir))

    # Next download all the additional dependencies
    for dep in info['additional_dependencies']:
        local('pip3 download --no-binary=:all: -d %s %s' %
              (tmp_app_dir, dep))
    add_dep_list_compressed = sorted(Path(tmp_app_dir).iterdir(),
                                     key=lambda f: f.stat().st_mtime)
    for it in range(len(add_dep_list_compressed)):
        add_dep_list_compressed[it] = os.path.basename(
            add_dep_list_compressed[it])

    # Download all the dependencies of the application
    # This first method should download all the dependencies needed
    # but for the local plateform !
    # --> Possible Issue during the installation in the remote
    # (it's not a cross-plateform install yet)
    local('pip3 download --no-binary=:all: -d %s git+%s@v%s' %
          (tmp_app_dir, info['repository'], info['version']))

    # Create  directory in the remote machine to store dependency packages
    run(
        template(
            "mkdir -p %s" % env.app_repository
        )
    )
    # Send the dependencies (and the dependencies of dependencies) to the
    # remote machine
    for whl in os.listdir(tmp_app_dir):
        local(
            template(
                "rsync -pthrvz -e 'ssh -p $port'  %s/%s \
                $username@$remote:$app_repository" % (tmp_app_dir, whl)
            )
            # "rsync -pthrvz %s/%s eagle:$app_repository"%(tmp_app_dir, whl)
        )

    # Set required env variable
    env.config = "Install_VECMA_App"
    # env.nodes = 1
    env.nodes = env.cores
    script = os.path.join(tmp_app_dir, "script")
    # Write the Install command in a file
    with open(script, "w") as sc:
        install_dir = ""
        if venv == 'True':
            # clean virtualenv and App_repo directory on remote machine side
            # To make sure everything is going to be installed from scratch
            '''
            sc.write("find %s/ -maxdepth 1 -mindepth 1 -type d \
                -exec rm -rf \"{}\" \\;\n" % (env.app_repository))
            sc.write("rm -rf %s\n" % (env.virtual_env_path))
            '''

            # It seems some version of python/virtualenv doesn't support
            # the option --no-download. So there is sometime a problem :
            # from pip import main
            # ImportError: cannot import name 'main'
            #
            # TODO Check python version and raised a Warning if not the
            # right version ?
            # TODO
            #
            sc.write("if [ ! -d %s ]; then \n\t bash %s/miniconda.sh -b -p %s \
                || echo 'WARNING : virtualenv is not installed \
                or has a problem' \nfi" %
                     (env.virtual_env_path,
                      env.app_repository, env.virtual_env_path))
            sc.write("\n\neval \"$$(%s/bin/conda shell.bash hook)\"\n\n" %
                     (env.virtual_env_path))
            # install_dir = ""
            '''
            with the latest version of numpy, I got this error:
            1. Check that you expected to use Python3.8 from ...,
                and that you have no directories in your PATH or PYTHONPATH
                that can interfere with the Python and numpy version "1.18.1"
                you're trying to use.
            so, since that we are using VirtualEnv, to avoid any conflict,
            it is better to clear PYTHONPATH
            '''
            # sc.write("\nexport PYTHONPATH=\"\"\n")
            sc.write("\nmodule unload python\n")

        # First install the additional_dependencies
        for dep in reversed(add_dep_list_compressed):
            print(dep)
            if dep.endswith('.zip'):
                sc.write("\nunzip %s/%s -d %s && cd %s/%s \
                    && %s/bin/python3 setup.py install %s\n"
                         % (env.app_repository, dep, env.app_repository,
                            env.app_repository, dep.replace(".zip", ""),
                            env.virtual_env_path, install_dir))
            elif dep.endswith('.tar.gz'):
                sc.write("\ntar xf %s/%s -C %s && cd %s/%s \
                    && %s/bin/python3 setup.py install %s\n"
                         % (env.app_repository, dep, env.app_repository,
                            env.app_repository, dep.replace(".tar.gz", ""),
                            env.virtual_env_path, install_dir))

        sc.write("%s/bin/pip install --no-index --no-build-isolation \
            --find-links=file:%s %s/%s-%s.zip %s \
            || %s/bin/pip install --no-index --find-links=file:%s %s/%s-%s.zip"
                 % (env.virtual_env_path,
                    env.app_repository, env.app_repository,
                    info['name'], info['version'],
                    install_dir,
                    env.virtual_env_path,
                    env.app_repository,
                    env.app_repository, info['name'], info['version']))

    # Add the tmp_app_dir directory in the local templates path because the
    # script is saved in it
    env.local_templates_path.insert(0, tmp_app_dir)

    install_dict = dict(script="script")
    # env.script = "script"
    update_environment(install_dict)

    # Determine a generated job name from environment parameters
    # and then define additional environment parameters based on it.
    env.job_results, env.job_results_local = with_template_job()

    # Create job script based on "sbatch header" and script created above in
    # deploy/.jobscript/

    env.job_script = script_templates(env.batch_header_install_app, env.script)

    # Create script's destination path to remote machine based on
    run(template("mkdir -p $scripts_path"))
    env.dest_name = env.pather.join(
        env.scripts_path, env.pather.basename(env.job_script)
    )

    # Send Install script to remote machine
    put(env.job_script, env.dest_name)
    #
    run(template("mkdir -p $job_results"))

    with cd(env.pather.dirname(env.job_results)):
        run(template("%s %s") % (env.job_dispatch, env.dest_name))

    local('rm -rf %s' % tmp_app_dir)
