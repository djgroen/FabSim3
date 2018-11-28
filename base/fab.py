# -*- coding: utf-8 -*-
#
#
# This source file is part of the FabSim software toolkit, which is
# distributed under the BSD 3-Clause license.
# Please refer to LICENSE for detailed information regarding the
# licensing.
#
# fab.py contains general-purpose FabSim routines.

from deploy.templates import *
from deploy.machines import *
from fabric.contrib.project import *
from base.manage_remote_job import *
from base.setup_fabsim import *
from fabric.api import settings
from xml.etree import ElementTree
import time
import re
import numpy as np
import yaml
import tempfile
import os.path
import subprocess
import math
from pprint import PrettyPrinter
pp = PrettyPrinter()


def get_plugin_path(name):
    """
    Get the local base path of plugin <name>.
    """
    return os.path.join(env.localroot, 'plugins', name)


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


def with_template_job():
    """
    Determine a generated job name from environment parameters,
    and then define additional environment parameters based on it.
    """
    name = template(env.job_name_template)
    if env.get('label'):
        name = '_'.join((env['label'], name))
    with_job(name)


def with_job(name):
    """Augment the fabric environment with information regarding a
    particular job name.

    Definitions created:
    job_results: the remote location where job results should be stored
    job_results_local: the local location where job results should be
      stored
    """
    env.name = name
    env.job_results = env.pather.join(env.results_path, name)
    env.job_results_local = os.path.join(env.local_results, name)
    env.job_results_contents = env.pather.join(env.job_results, '*')
    env.job_results_contents_local = os.path.join(env.job_results_local, '*')


def with_template_config():
    """
    Determine the name of a used or generated config from environment
    parameters, and then define additional environment parameters based
    on it.
    """
    with_config(template(env.config_name_template))


def find_config_file_path(name):
    path_used = None
    for p in env.local_config_file_path:
        config_file_path = os.path.join(p, name)
        if os.path.exists(config_file_path):
            path_used = config_file_path

    if path_used is None:
        raise Exception(
            "Error: config file directory not found in: ",
            env.local_config_file_path
            )
    return path_used


def with_config(name):
    """Internal: augment the fabric environment with information
      regarding a particular configuration name.
    Definitions created:
    job_config_path: the remote location where the config files
      for the job should be stored
    job_config_path_local: the local location where the config files
      for the job may be found
    """
    env.config = name
    env.job_config_path = env.pather.join(env.config_path, name)

    path_used = find_config_file_path(name)

    env.job_config_path_local = os.path.join(path_used)
    env.job_config_contents = env.pather.join(env.job_config_path, '*')
    env.job_config_contents_local = os.path.join(
        env.job_config_path_local, '*'
        )
    # name of the job sh submission script.
    env.job_name_template_sh = template("%s.sh" % env.job_name_template)


def with_profile(name):
    """Internal: augment the fabric environment with information
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
        env.profiles_path, name
        )
    env.job_profile_path_local = os.path.join(
        env.local_profiles, name
        )
    env.job_profile_contents = env.pather.join(
        env.job_profile_path, '*'
        )
    env.job_profile_contents_local = os.path.join(
        env.job_profile_path_local, '*'
        )


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
def put_configs(config='', skip_sweep_dir=False):
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
    if env.manual_gsissh:
        if skip_sweep_dir:
            print(
                "Warning: skip_sweep_dir is not supported when using \
                FabSim3 with Globus. This is because the Globus developers \
                did not bother to support the option to exclude specific \
                directories with globus-url-copy (unlike the rsync \
                developers)."
                )
        local(
            template(
                "globus-url-copy -p 10 -cd -r -sync \
                file://$job_config_path_local/ \
                gsiftp://$remote/$job_config_path/"
                )
            )
    else:
        if skip_sweep_dir:
            rsync_project(
                local_dir=env.job_config_path_local + '/',
                remote_dir=env.job_config_path,
                exclude=["SWEEP"]
                )
        else:
            rsync_project(
                local_dir=env.job_config_path_local + '/',
                remote_dir=env.job_config_path
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
    with_job(name)
    if env.manual_gsissh:
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
                "rsync -pthrvz $username@$remote:$job_results/%s \
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

    """
    Sets up directories required for the use of FabSim.
    """
    """
    Creates the necessary fab dirs remotely.
    """
    run(template(get_setup_fabsim_dirs_string()))


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


def job(*option_dictionaries):
    """
    Internal low level job launcher.
    Parameters for the job are determined from the prepared fabric environment
    Execute a generic job on the remote machine. Use hemelb, regress, or test
    instead.
    """

    env.fabsim_git_hash = get_fabsim_git_hash()

    env.submit_time = time.strftime('%Y%m%d%H%M%S')
    time.sleep(1.)
    update_environment(*option_dictionaries)
    with_template_job()
    # Use this to request more cores than we use, to measure performance
    # without sharing impact
    if env.get('cores_reserved') == 'WholeNode' and env.get('corespernode'):
        env.cores_reserved = (
            (1 + (int(env.cores) - 1) / int(env.corespernode)) *
            env.corespernode
            )
    # If cores_reserved is not specified, temporarily set it based on the
    # same as the number of cores
    # Needs to be temporary if there's another job with a different number
    # of cores which should also be defaulted to.
    with settings(cores_reserved=env.get('cores_reserved') or env.cores):
        # Make sure that prefix and module load definitions are properly
        # updated.
        complete_environment()

        calc_nodes()
        if env.node_type:
            env.node_type_restriction = template(
                env.node_type_restriction_template
                )
        env['job_name'] = env.name[0:env.max_job_name_chars]
        with settings(cores=1):
            calc_nodes()
            env.run_command_one_proc = template(env.run_command)
        calc_nodes()
        env.run_command = template(env.run_command)
        env.job_script = script_templates(env.batch_header, env.script)

        env.dest_name = env.pather.join(
            env.scripts_path, env.pather.basename(env.job_script)
            )
        put(env.job_script, env.dest_name)

        # Store previous fab commands in bash history.
        env.fabsim_command_history = get_fabsim_command_history()
        # Make directory, copy input files and job script to results directory
        run(
            template(
                "mkdir -p $job_results && rsync -av --progress \
                $job_config_path/* $job_results/ --exclude SWEEP && \
                cp $dest_name $job_results"
                )
            )
        env = removekey(removekey(dict(env), 'passwords'), 'password')
        with tempfile.NamedTemporaryFile(mode='r+') as tempf:
            tempf.write(
                yaml.dump(dict(env))
                )
            tempf.flush()  # Flush the file before we copy it.
            put(tempf.name, env.pather.join(env.job_results, 'env.yml'))
        run(template("chmod u+x $dest_name"))
        # Allow option to submit all preparations, but not actually submit
        # the job
        if not env.get("noexec", False):
            with cd(env.job_results):
                with prefix(env.run_prefix):
                    run(template("$job_dispatch $dest_name"))
        print(
            "JOB OUTPUT IS STORED REMOTELY IN: %s:%s " %
            (env.remote, env.job_results)
            )
        print(
            "Use `fab %s fetch_results` to copy the results back to %s on\
            localhost." %
            (env.machine_name, env.job_results_local)
            )
    if env.get("dumpenv",False) == "True":
        print("DUMPENV mode enabled. Dumping environment:")
        print(env)


def run_ensemble(config, sweep_dir, **args):
    """Map and execute ensemble jobs.
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

    with_config(config)

    sweep_length = 0  # number of runs performed in this sweep

    for item in os.listdir(sweep_dir):
        if os.path.isfile(os.path.join(sweep_dir, item)):
            sweep_length += 1
            # copy file_ to config directory
            if "input_name_in_config" in env:
                local(
                    template("cp %s %s/%s") % (
                        os.path.join(sweep_dir, item),
                        env.job_config_path_local, env.input_name_in_config)
                    )
            else:
                local(
                    template("cp %s %s/") % (
                        os.path.join(sweep_dir, item),
                        env.job_config_path_local)
                    )
            execute(put_configs, config, skip_sweep_dir=True)
            job(dict(wall_time='0:15:0', memory='2G', label=item), args)
        if os.path.isdir(os.path.join(sweep_dir, item)):
            sweep_length += 1
            # copy file_ to config directory
            local(
                template("cp -r %s/* %s/") % (
                    os.path.join(sweep_dir, item), env.job_config_path_local)
                )
            execute(put_configs, config, skip_sweep_dir=True)
            job(dict(wall_time='0:15:0', memory='2G', label=item), args)
    if sweep_length == 0:
        print(
            "ERROR: no files where found in the sweep_dir of this\
            run_ensemble command."
            )
        print("Sweep dir location: %s" % (sweep_dir))


def input_to_range(arg, default):
    ttype = type(default)
    # regexp for a array generator like [1.2:3:0.2]
    gen_regexp = "\[([\d\.]+):([\d\.]+):([\d\.]+)\]"
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
    if env.manual_gsissh:
        return manual_gsissh(cmd)
    elif env.manual_ssh:
        return manual(cmd)
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
            template(
                "globus-url-copy -sync -r -cd -p 10\
                file://$manual_src gsiftp://$host/$manual_dest"
                )
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
        env.local_blackbox_path
        )


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
    print(
        "REMOTE MOVE: mv %s/%s %s/Backup" % (
            env.results_path, prefix, parent_path
            )
        )
    run("mkdir -p %s/Backup" % (parent_path))
    run(
        "mv -i %s/%s* %s/Backup/" % (env.results_path, prefix, parent_path)
        )


@task
def print_config(args=''):
    """ Prints local environment """
    for x in env:
        print(x, ':', env[x])
