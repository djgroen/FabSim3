import math
import os
import re
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path
from pprint import pformat, pprint
from shutil import copy, copyfile, rmtree

import numpy as np
from beartype import beartype
from beartype.typing import Callable, Optional, Tuple, Union
from rich import print as rich_print
from rich.console import Console
from rich.panel import Panel
from rich.table import Table, box

# from fabsim.base.utils import add_prefix, print_prefix
from fabsim.base.decorators import load_plugin_env_vars, task
from fabsim.base.env import env
from fabsim.base.manage_remote_job import *
from fabsim.base.MultiProcessingPool import MultiProcessingPool
from fabsim.base.networks import local, put, rsync_project, run
from fabsim.base.setup_fabsim import *
from fabsim.deploy.machines import *
from fabsim.deploy.templates import (
    script_template_content,
    script_templates,
    template,
)


@beartype
def get_plugin_path(name: str) -> str:
    """
    Get the local base path of input plugin name.

    Args:
        name (str): the name of pluing

    Returns:
        str: the path of plugin

    Raises:
        RuntimeError: if the requested plugin is not installed in the
            local system
    """
    plugin_path = os.path.join(env.localroot, "plugins", name)
    if not os.path.exists(plugin_path):
        raise RuntimeError(
            f"The requested plugin {name} does not exist ({plugin_path}).\n"
            "you can install it by typing:\n\t"
            f"fabsim localhost install_plugin:{name}"
        )
    return plugin_path


@task
@beartype
def put_results(name: str) -> None:
    """
    Transfer result files to a remote. Local path to find result
    directories is specified in machines_user.json. This method is not
    intended for normal use, but is useful when the local machine
    cannot have an entropy mount, so that results from a local machine
    can be sent to entropy, via 'fab legion fetch_results; fab entropy
    put_results'

    Args:
        name (str, optional): the name of results directory
    """
    with_job(name)
    run(template("mkdir -p $job_results"))
    if env.manual_gsissh:
        local(
            template(
                "globus-url-copy -p 10 -cd -r -sync "
                "file://$job_results_local/ "
                "gsiftp://$remote/$job_results/"
            )
        )
    else:
        rsync_project(
            local_dir=env.job_results_local + "/", remote_dir=env.job_results
            )


@task
@beartype
def fetch_results(
    name: Optional[str] = "",
    regex: Optional[str] = "",
    files: Optional[str] = None,
    debug: Optional[bool] = False,
) -> None:
    """
    Fetch results of remote jobs to local result store. Specify a job
    name to transfer just one job. Local path to store results is
    specified in machines_user.json, and should normally point to a
    mount on entropy, i.e. /store4/blood/username/results.
    If you can't mount entropy, `put results` can be useful, via
    `fab legion fetch_results; fab entropy put_results`

    Args:
        name (str, optional): the job name, it no name provided, all
            directories from `fabric_dir` will be fetched
        regex (str, optional): the matching pattern
        files (str, optional): the list of files need to fetched from the
            remote machine. The list of file should be passed as string, and
            split by `;`. For example, to fetch only `out.csv` and `env.yml`
            files, you should pass `files="out.csv;env.yml" to this function.
        debug (bool, optional): it `True`, all `env` variable will shown.
    """
    fetch_files = []
    if files is not None:
        fetch_files = files.split(";")
    includes_files = ""
    if len(fetch_files) > 0:
        includes_files = " ".join(
            [
                *["--include='*/' "],
                *["--include='{}' ".format(file) for file in fetch_files],
                *["--exclude='*'  "],
                *["--prune-empty-dirs "],
            ]
        )

    env.job_results, env.job_results_local = with_job(name)

    # check if the local results directory exists or not
    if not os.path.isdir(env.job_results_local):
        os.makedirs(env.job_results_local)

    if env.manual_sshpass:
        sshpass_args = "-e" if env.env_sshpass else "-f $sshpass"
        local(
            template(
                "rsync -pthrvz -e 'sshpass {} ssh -p $port' {}"
                "$username@$remote:$job_results/{}  "
                "$job_results_local".format(
                    sshpass_args, includes_files, regex
                )
            )
        )
    elif env.manual_gsissh:
        local(
            template(
                "globus-url-copy -cd -r -sync {}"
                "gsiftp://$remote/$job_results/{} "
                "file://$job_results_local/".format(includes_files, regex)
            )
        )
    else:
        local(
            template(
                "rsync -pthrvz -e 'ssh -p $port' {}"
                "$username@$remote:$job_results/{} "
                "$job_results_local".format(includes_files, regex)
            )
        )


@task
@beartype
def fetch_configs(config: str) -> None:
    """
    Fetch config files from the remote machine, via `rsync`.

    Example Usage:

    ```sh
    fab eagle_vecma fetch_configs:mali
    ```

    Args:
        config (str): the name of config directory
    """
    with_config(config)
    if env.manual_gsissh:
        local(
            template(
                "globus-url-copy -cd -r -sync "
                "gsiftp://$remote/$job_config_path/ "
                "file://$job_config_path_local/"
            )
        )
    else:
        local(
            template(
                "rsync -pthrvz $username@$remote:$job_config_path/ "
                "$job_config_path_local"
            )
        )


@task
@beartype
def clear_results(name: str) -> None:
    """
    Completely wipe all result files from the remote.

    Args:
        name (str, optional): the name of result folder
    """
    with_job(name)
    run(template("rm -rf $job_results_contents"))


@beartype
def execute(task: Callable, *args, **kwargs) -> None:
    """
    Execute a task (callable function).
    The input arg `task` can be an actual callable function or its name.

    The target function can be warped by @task or not.

    """
    f_globals = inspect.stack()[1][0].f_globals
    if callable(task):
        task(*args, **kwargs)
    elif task in f_globals:
        f_globals[task](*args, **kwargs)
    else:
        msg = (
            "The request task [green3]{}[/green3] passed to execute() "
            "function can not be found !!!".format(task)
        )
        console = Console()
        console.print(
            Panel(
                "{}".format(msg),
                title="[red1]Error[/red1]",
                border_style="red1",
                expand=False,
            )
        )


@beartype
def put_configs(config: str) -> None:
    """
    Transfer config files to the remote machine, via `rsync`.

    Args:
        config (str): Specify a config directory
    """
    with_config(config)

    # by using get_setup_fabsim_dirs_string(), the FabSim3 directories will
    # created automatically whenever a config file is uploaded.

    run(
        template("{}; mkdir -p $job_config_path".format(
            get_setup_fabsim_dirs_string()
            )
        )
    )

    rsync_delete = False
    if (
        hasattr(env, "prevent_results_overwrite")
        and env.prevent_results_overwrite == "delete"
    ):
        rsync_delete = True

    if env.ssh_monsoon_mode:
        # scp a monsoonfab:~/ ; ssh monsoonfab -C “scp ~/a xcscfab:~/”
        local(
            template(
                "scp -r $job_config_path_local "
                "$remote:$config_path/ && "
                "ssh $remote -C "
                "'scp -r $job_config_path "
                "$remote_compute:$config_path/'"
            )
        )

    elif env.manual_sshpass:
        sshpass_args = "-e" if env.env_sshpass else "-f $sshpass"
        local(
            template(
                f"rsync -pthrvz --rsh='sshpass {sshpass_args} ssh  -p 22  ' "
                "$job_config_path_local/ "
                "$username@$remote:$job_config_path/"
            )
        )
    elif env.manual_ssh:
        local(
            template(
                "rsync -pthrvz "
                "$job_config_path_local/ "
                "$username@$remote:$job_config_path/"
            )
        )
    elif env.manual_gsissh:
        # TODO: implement prevent_results_overwrite here
        local(
            template(
                "globus-url-copy -p 10 -cd -r -sync "
                "file://$job_config_path_local/ "
                "gsiftp://$remote/$job_config_path/"
            )
        )
    else:
        rsync_project(
            local_dir=env.job_config_path_local + "/",
            remote_dir=env.job_config_path,
            delete=rsync_delete,
        )


def calc_nodes() -> None:
    """
    Calculate the required number of node needs for the job execution.
    This will set the `env.nodes` which will be used to set the node request
    number in the job script.

    !!! tip
        If we're not reserving whole nodes, then if we request less than one
        node's worth of cores, need to keep N<=n
    """
    env.coresusedpernode = env.corespernode
    if int(env.coresusedpernode) > int(env.cores):
        env.coresusedpernode = env.cores
    env.nodes = int(math.ceil(float(env.cores) / float(env.coresusedpernode)))


def calc_total_mem() -> None:
    """
    Calculate the total amount of memory for the job script.

    !!! tip
        in terms of using `PJ` option, please make sure you set the total
        required memory for all sub-tasks.

    """
    # for qcg scheduler, #QCG memory requires total memory for all nodes
    if not hasattr(env, "memory"):
        env.memory = "2GB"

    mem_size = int(re.findall("\\d+", str(env.memory))[0])
    try:
        mem_unit_str = re.findall("[a-zA-Z]+", str(env.memory))[0]
    except Exception:
        mem_unit_str = ""

    if mem_unit_str.upper() == "GB" or mem_unit_str.upper() == "G":
        mem_unit = 1000
    else:
        mem_unit = 1

    if hasattr(env, "PJ") and env.PJ.lower() == "true":
        # env.total_mem = mem_size * int(env.PJ_size) * mem_unit
        env.total_mem = env.memory
    else:
        env.total_mem = mem_size * int(env.nodes) * mem_unit


@beartype
def find_config_file_path(
    name: str,
    ExceptWhenNotFound: Optional[bool] = True
) -> str:
    """
    Find the config file path

    Args:
        name (str): the name of config directory
        ExceptWhenNotFound (bool, optional): if `True`, raise an exception when the input config name not found. Defaults to `True`.

    Returns:
        Union[bool, str]: - `False`: if the input config name not found
        - the path of input config name
    """
    # Prevent of executing localhost runs on the FabSim3 root directory
    if env.host == "localhost" and env.work_path == env.fabsim_root:
        msg = (
            "The localhost run dir is same as your FabSim3 folder\n"
            "To avoid any conflict of config folder, please consider\n"
            "changing your home_path_template variable\n"
            "you can easily modify it by updating localhost entry in\n"
            "your FabSim3/fabsim/deploy/machines_user.yml file\n\n"
            "Here is the suggested changes:\n\n"
        )

        solution = "localhost:\n"
        solution += "   ...\n"
        solution += '   home_path_template: "{}/localhost_exe"'.format(
            env.localroot
        )
        rich_print(
            Panel(
                "{}[green3]{}[/green3]".format(msg, solution),
                title="[red1]Error[/red1]",
                border_style="red1",
                expand=False,
            )
        )
        exit()

    path_used = None
    for p in env.local_config_file_path:
        config_file_path = os.path.join(p, name)
        if os.path.exists(config_file_path):
            path_used = config_file_path

    if path_used is None:
        if ExceptWhenNotFound:
            raise Exception(
                "Error: config file directory '{}' " "not found in: ".format(
                    name
                ),
                env.local_config_file_path,
            )
        else:
            return False
    return path_used


@beartype
def with_config(name: str):
    """
    Internal: augment the fabric environment with information
      regarding a particular configuration name.

    Definitions created:

    - `job_config_path`: the remote location where the config files for the
            job should be stored
    - `job_config_path_local`: the local location where the config files for
            the job may be found

    Args:
        name (str): the name of config directory
    """
    env.config = name
    env.job_config_path = os.path.join(env.config_path, name + env.job_desc)

    path_used = find_config_file_path(name)

    env.job_config_path_local = os.path.join(path_used)
    env.job_config_contents = os.path.join(env.job_config_path, "*")
    env.job_config_contents_local = os.path.join(
        env.job_config_path_local, "*"
    )
    # name of the job sh submission script.
    env.job_name_template_sh = template("{}.sh".format(env.job_name_template))


@beartype
def add_local_paths(plugin_name: str) -> None:
    """
    Updates `env` variables for the input plugin name

    Args:
        plugin_name (str): plugin name
    """
    # This variable encodes the default location for templates.
    env.local_templates_path.insert(
        0, os.path.join(env.localroot, "plugins", plugin_name, "templates")
    )
    # This variable encodes the default location for config files.
    env.local_config_file_path.insert(
        0, os.path.join(env.localroot, "plugins", plugin_name, "config_files")
    )


@beartype
def with_template_job(
    ensemble_mode: Optional[bool] = False, label: Optional[str] = None
) -> Tuple[str, str]:
    """
    Determine a generated job name from environment parameters,
    and then define additional environment parameters based on it.

    Args:
        ensemble_mode (bool, optional): determines if the job is an ensemble
            simulation or not
        label (str, optional): the label of job

    Returns:
        Tuple[str, str]: returns `job_results, job_results_local` env variables
            filled based on job and label name
    """

    # The name is now depending of the label name
    name = template(env.job_name_template)
    if label and not ensemble_mode:
        name = "_".join((label, name))

    job_results, job_results_local = with_job(
        name=name, ensemble_mode=ensemble_mode, label=label
    )

    return job_results, job_results_local


@beartype
def with_job(
    name: str,
    ensemble_mode: Optional[bool] = False,
    label: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Augment the fabric environment with information regarding a particular
    job name.

    Definitions created:

    - `job_results`: the remote location where job results should be stored
    - `job_results_local`: the local location where job results should be
          stored


    Args:
        name (str): the job name
        ensemble_mode (bool, optional): determines if the job is an ensemble
            simulation or not
        label (str, optional): the label of job

    Returns:
        Tuple[str, str]: two string value

        - job_results: the remote location where job results should be stored
        - job_results_local: the local location where job results should
            be stored
    """
    env.name = name
    if not ensemble_mode:
        job_results = env.pather.join(env.results_path, name)
        job_results_local = os.path.join(env.local_results, name)
    else:
        job_results = "{}/RUNS/{}".format(
            env.pather.join(env.results_path, name), label
        )
        job_results_local = "{}/RUNS/{}".format(
            os.path.join(env.local_results, name), label
        )

    env.job_results_contents = env.pather.join(job_results, "*")
    env.job_results_contents_local = os.path.join(job_results_local, "*")

    # Template name is now depending of the label of the job when needed
    if label is not None:
        env.job_name_template_sh = "{}_{}.sh".format(name, label)
    else:
        env.job_name_template_sh = "{}.sh".format(name)

    return job_results, job_results_local


def with_template_config() -> None:
    """
    Determine the name of a used or generated config from environment
    parameters, and then define additional environment parameters based
    on it.
    """
    with_config(template(env.config_name_template))


def job(*job_args, prepare_only=False):
    """
    Internal low level job launcher.
    Parameters for the job are determined from the prepared fabric environment
    Execute a generic job on the remote machine.

    To improve the total job submission, and reduce the number of SSH
    connection for job files/folders transmission, the job submission workflow
    divided into 3 individual sub-tasks:

    1. job_preparation
    2. job_transmission
    3. job_submission

    Returns the generate jobs scripts for submission on the remote machine.
    """
    args = {}
    for adict in job_args:
        args = dict(args, **adict)

    # check if with_config function is already called or not
    if not hasattr(env, "job_config_path"):
        raise RuntimeError(
            "Function with_config did NOT called, "
            "Please call it before calling job()"
        )

    update_environment(args)
    #   Add label, mem, core to env.
    calc_nodes()
    calc_total_mem()

    if "sweepdir_items" in args:
        env.ensemble_mode = True
    else:
        env.ensemble_mode = False

    ########################################################
    #  temporary folder to save job files/folders/scripts  #
    ########################################################
    env.tmp_work_path = env.pather.join(
        tempfile._get_default_tempdir(),
        next(tempfile._get_candidate_names()),
        "FabSim3",
        # env.fabric_dir
    )

    if os.path.exists(env.tmp_work_path):
        rmtree(env.tmp_work_path)
    # the config_files folder is already transfered by put_config
    env.tmp_results_path = env.pather.join(env.tmp_work_path, "results")
    env.tmp_scripts_path = env.pather.join(env.tmp_work_path, "scripts")
    os.makedirs(env.tmp_scripts_path)
    os.makedirs(env.tmp_results_path)

    POOL = MultiProcessingPool(PoolSize=int(env.nb_process))

    #####################################
    #       job preparation phase       #
    #####################################
    msg = "tmp_work_path = {}".format(env.tmp_work_path)
    rich_print(
        Panel.fit(
            msg,
            title="[orange_red1]job preparation phase[/orange_red1]",
            border_style="orange_red1",
        )
    )

    print("Submit tasks to multiprocessingPool : start ...")

    print("args", args)

    if "replica_start_number" in args:
        if isinstance(args["replica_start_number"], list):
            env.replica_start_number = list(
                int(x) for x in args["replica_start_number"]
            )
        else:
            env.replica_start_number = int(args["replica_start_number"])
    else:
        env.replica_start_number = 1

    if env.ensemble_mode is True:
        for index, task_label in enumerate(env.sweepdir_items):
            if isinstance(env.replica_start_number, list):
                replica_start_number = env.replica_start_number[index]
            else:
                replica_start_number = env.replica_start_number

            POOL.add_task(
                func=job_preparation,
                func_args=dict(
                    ensemble_mode=env.ensemble_mode,
                    label=task_label,
                    replica_start_number=replica_start_number,
                ),
            )
    else:
        args["replica_start_number"] = env.replica_start_number
        POOL.add_task(func=job_preparation, func_args=args)

    print("Submit tasks to multiprocessingPool : done ...")
    job_scripts_to_submit = POOL.wait_for_tasks()

    if prepare_only:
        return job_scripts_to_submit

    #####################################
    #       job transmission phase      #
    #####################################
    msg = (
        "Copy all generated files/folder from\n"
        "tmp_work_path = {}\n"
        "to\n"
        "work_path = {}".format(env.tmp_work_path, env.work_path)
    )
    rich_print(
        Panel.fit(
            msg,
            title="[orange_red1]job transmission phase[/orange_red1]",
            border_style="orange_red1",
        )
    )
    job_transmission()

    if not (hasattr(env, "TestOnly") and env.TestOnly.lower() == "true"):
        # DO NOT submit any job
        # env.submit_job is False in case of using PilotJob option
        # therefore, DO NOT submit the job directly, only submit PJ script
        if not (
            hasattr(env, "submit_job")
            and isinstance(env.submit_job, bool)
            and env.submit_job is False
        ):
            #####################################
            #       job submission phase      #
            #####################################
            msg = "Submit all generated job scripts to target remote machine"
            rich_print(
                Panel.fit(
                    msg,
                    title="[orange_red1]job submission phase[/orange_red1]",
                    border_style="orange_red1",
                )
            )
            for job_script in job_scripts_to_submit:
                job_submission(dict(job_script=job_script))
            print("submitted job script = \n{}".format(
                pformat(job_scripts_to_submit)
                )
            )

    # POOL.shutdown_threads()
    return job_scripts_to_submit


def job_preparation(*job_args):
    """
    here, all job folders and scripts will be created in the temporary folder
        `<tmp_folder>/{results,scripts}`, later, in job_transmission,
    we transfer all these files and folders with a single `rsync` command.
    This approach will helps us to reduce the number of SSH connection and
    improve the stability of job submission workflow which can be compromised
    by high parallel SSH connection
    """
    pprint(job_args)

    args = {}
    for adict in job_args:
        args = dict(args, **adict)

    if "label" in args:
        env.label = args["label"]
    else:
        env.label = ""

    return_job_scripts = []

    for i in range(
        args["replica_start_number"],
        int(env.replicas) + args["replica_start_number"],
    ):
        env.replica_number = i

        env.job_results, env.job_results_local = with_template_job(
            ensemble_mode=env.ensemble_mode, label=env.label
        )

        if int(env.replicas) > 1:
            if env.ensemble_mode is False:
                env.job_results += "_replica_" + str(i)
            else:
                env.job_results += "_" + str(i)

        tmp_job_results = env.job_results.replace(
            env.results_path, env.tmp_results_path
        )

        env["job_name"] = env.name[0: env.max_job_name_chars]
        complete_environment()

        env.run_command = template(env.run_command)

        if env.label not in ["PJ_PYheader", "PJ_header"]:
            env.run_prefix += (
                "\n\n"
                "# copy files from config folder\n"
                "config_dir={}\n"
                "rsync -pthrvz --inplace --exclude SWEEP "
                "$config_dir/* .".format(env.job_config_path)
            )

        if env.ensemble_mode:
            env.run_prefix += (
                "\n\n"
                "# copy files from SWEEP folder\n"
                "rsync -pthrvz --inplace $config_dir/SWEEP/{}/ .".format(
                    env.label
                )
            )

        if not (hasattr(env, "venv") and str(env.venv).lower() == "true"):
            if hasattr(env, "py_pkg") and len(env.py_pkg) > 0:
                env.run_prefix += (
                    "\n\n"
                    "# Install requested python packages\n"
                    "pip3 install --user --upgrade {}".format(
                        " ".join(pkg for pkg in env.py_pkg)
                    )
                )

        # this is a tricky situation,
        # in case of ensemble runs, or simple job, we need to add env.label
        # to generated job script name,
        # however, for PJ_PYheader and PJ_header header script, nothing should
        # be added at the end of script file name, so, here we pass a empty
        # string as label
        if hasattr(env, "NoEnvScript") and env.NoEnvScript:
            tmp_job_script = script_templates(env.batch_header)
        else:
            tmp_job_script = script_templates(env.batch_header, env.script)

        # Separate base from extension
        base, extension = os.path.splitext(env.pather.basename(tmp_job_script))
        # Initial new name if we have replicas or ensemble

        if int(env.replicas) > 1:
            if env.ensemble_mode is False:
                dst_script_name = base + "_replica_" + str(i) + extension
            else:
                dst_script_name = base + "_" + str(i) + extension
        else:
            dst_script_name = base + extension

        dst_job_script = env.pather.join(env.tmp_scripts_path, dst_script_name)

        # Add target job script to return list

        """
        return_job_scripts.append(env.pather.join(env.scripts_path,
                                               dst_script_name)
        """
        # here, instead of returning PATH to script folder, it is better to
        # submit script from results_path folder, specially in case of PJ job
        return_job_scripts.append(
            env.pather.join(env.job_results, dst_script_name)
        )

        copy(tmp_job_script, dst_job_script)
        # chmod +x dst_job_script
        # 755 means read and execute access for everyone and also
        # write access for the owner of the file
        os.chmod(dst_job_script, 0o755)

        os.makedirs(tmp_job_results, exist_ok=True)
        copy(dst_job_script, env.pather.join(tmp_job_results, dst_script_name))

        # TODO: these env variables are not used anywhere
        # TODO: maybe it is better to remove them
        # job_name_template_sh
        # job_results_contents
        # job_results_contents_local
        with open(
            env.pather.join(tmp_job_results, "env.yml"
                            ), "w") as env_yml_file:
            yaml.dump(
                dict(
                    env,
                    **{
                        "sshpass": None,
                        "passwords": None,
                        "password": None,
                        "sweepdir_items": None,
                    },
                ),
                env_yml_file,
                default_flow_style=False,
            )

    return return_job_scripts


def job_transmission(*job_args):
    """
    here, we only transfer all generated files/folders from

    `<tmp_folder>/{results,scripts}`

    to

    `<target_work_dir>/{results,scripts}`
    """
    args = {}
    for adict in job_args:
        args = dict(args, **adict)

    if (
        hasattr(env, "prevent_results_overwrite")
        and env.prevent_results_overwrite == "delete"
    ):
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
            print("empty folder: ", empty_folder)
            print("results_dir_item: ", results_dir_item)
            if env.ssh_monsoon_mode:
                task_string = template(
                    "mkdir -p {} && "
                    "mkdir -p {}/results/{} && "
                    "rm -rf {}/results/{}/*".format(
                        empty_folder,
                        env.work_path,
                        results_dir_item,
                        env.work_path,
                        results_dir_item,
                    )
                )

                run(
                    template(
                        "{} ; ssh $remote_compute -C"
                        "'{}'".format(
                            task_string,
                            task_string,
                        )
                    )
                )

            else:
                run(
                    template(
                        "mkdir -p {} && "
                        "mkdir -p {}/results &&"
                        "rsync -a --delete --inplace {}/ "
                        "{}/results/{}/".format(
                            empty_folder,
                            env.work_path,
                            empty_folder,
                            env.work_path,
                            results_dir_item,
                        )
                    )
                )

    rsyc_src_dst_folders = []
    rsyc_src_dst_folders.append((env.tmp_scripts_path, env.scripts_path))
    rsyc_src_dst_folders.append((env.tmp_results_path, env.results_path))

    for sync_src, sync_dst in rsyc_src_dst_folders:
        if env.ssh_monsoon_mode:
            # local(
            #    template(
            #        "scp -r "
            #        "{}/* $username@$remote:{}/ ".format(sync_src, sync_dst)
            #    )
            # )
            # scp a monsoonfab:~/ ; ssh monsoonfab -C “scp ~/a xcscfab:~/”
            local(
                template(
                    "ssh $remote -C "
                    "'mkdir -p {}' && "
                    "scp -r {} "
                    "$username@$remote:{}/../ && "
                    "ssh $remote -C "
                    "'scp -r {} "
                    "$remote_compute:{}/../'".format(
                        sync_dst,
                        sync_src,
                        sync_dst,
                        sync_dst,
                        sync_dst,
                    )
                )
            )
        elif env.manual_sshpass:
            sshpass_args = "-e" if env.env_sshpass else "-f $sshpass"
            # TODO: maybe the better option here is to overwrite the
            #       rsync_project
            local(
                template(
                    "rsync -pthrvz "
                    f"--rsh='sshpass {sshpass_args} ssh  -p 22  ' "
                    "{}/ $username@$remote:{}/ ".format(sync_src, sync_dst)
                )
            )
        elif env.manual_gsissh:
            # TODO: implement prevent_results_overwrite for this option
            local(
                template(
                    "globus-url-copy -p 10 -cd -r -sync "
                    "file://{}/ "
                    "gsiftp://$remote/{}/".format(sync_src, sync_dst)
                )
            )
        else:
            rsync_project(local_dir=sync_src + "/", remote_dir=sync_dst)


def job_submission(*job_args):
    """
    here, all prepared job scrips will be submitted to the
    target remote machine

    !!! note
        please make sure to pass the list of job scripts be summited as
        an input to this function
    """
    CRED = "\33[31m"
    CEND = "\33[0m"
    args = {}
    for adict in job_args:
        args = dict(args, **adict)

    job_script = args["job_script"]

    if (
        hasattr(env, "dispatch_jobs_on_localhost")
        and isinstance(env.dispatch_jobs_on_localhost, bool)
        and env.dispatch_jobs_on_localhost
    ):
        local(template("$job_dispatch " + job_script))
        print("job dispatch is done locally\n")

    elif not env.get("noexec", False):
        if env.dry_run:
            if env.host == "localhost":
                print("Dry run")
                subprocess.call(["cat", job_script])
            else:
                print("Dry run available only on localhost")
            exit()

        elif env.remote == "localhost":
            run(
                cmd="{} && {}".format(
                    env.run_prefix,
                    template("$job_dispatch {}".format(job_script)),
                ),
                cd=env.pather.dirname(job_script),
            )
        elif env.ssh_monsoon_mode:
            cmd = template(
                "ssh $remote_compute " "-C '$job_dispatch {}'".format(
                    job_script
                ),
                # Allow for variable references in job_dispatch definition
                number_of_iterations=2,
            )
            run(cmd, cd=env.pather.dirname(job_script))
        else:
            run(
                cmd=template(
                    "$job_dispatch {}".format(job_script),
                    # Allow for variable references in job_dispatch definition
                    number_of_iterations=2,
                ),
                cd=env.pather.dirname(job_script),
            )

    # print(
    #     "Use `fab {} fetch_results` to copy the results "
    #     "back to localhost.".format(env.machine_name)
    # )
    print(
        "Use "
        + CRED
        + "fabsim {} fetch_results".format(env.machine_name)
        + CEND
        + " to copy the results "
        "back to local machine!"
    )

    return [job_script]


@task
@beartype
def ensemble2campaign(
    results_dir: str, campaign_dir: str, skip: Optional[Union[int, str]] = 0
) -> None:
    """
    Converts FabSim3 ensemble results to EasyVVUQ campaign definition.
    results_dir: FabSim3 results root directory
    campaign_dir: EasyVVUQ root campaign directory.
    skip: The number of runs (run_1 to run_skip) not to copy to the campaign
    """
    # update_environment(args)
    # if skip > 0: only copy the run directories run_X for X > skip back
    # to the EasyVVUQ campaign dir
    if int(skip) > 0:
        # all run directories
        runs = os.listdir("{}/RUNS/".format(results_dir))
        for run in runs:
            # extract X from run_X
            run_id = int(run.split("_")[-1])
            # if X > skip copy results back
            if run_id > int(skip):
                local(
                    "rsync -pthrvz {}/RUNS/{} {}/runs".format(
                        results_dir, run, campaign_dir
                    )
                )
    # copy all runs from FabSim results directory to campaign directory
    else:
        local("rsync -pthrvz {}/RUNS/ {}/runs".format(
            results_dir, campaign_dir)
        )


@task
@beartype
def campaign2ensemble(
    config: str, campaign_dir: str, skip: Optional[Union[int, str]] = 0
) -> None:
    """
    Converts an EasyVVUQ campaign run set TO a FabSim3 ensemble definition.

    Args:
        config (str): FabSim3 configuration name (will create in top level if
            non-existent, and overwrite existing content).
        campaign_dir (str): EasyVVUQ root campaign directory
        skip (Union[int, str], optional): The number of runs(run_1 to run_skip)
            not to copy to the FabSim3 sweep directory. The first skip number
            of samples will then not be computed.
    """
    # update_environment(args)
    config_path = find_config_file_path(config, ExceptWhenNotFound=False)
    if config_path is False:
        local("mkdir -p {}/{}".format(env.local_config_file_path[-1], config))
        config_path = "{}/{}".format(env.local_config_file_path[-1], config)
    sweep_dir = config_path + "/SWEEP"
    local("mkdir -p {}".format(sweep_dir))

    local("rm -rf {}/*".format(sweep_dir))

    # if skip > 0: only copy the run directories run_X for X > skip to the
    # FabSim3 sweep directory. This avoids recomputing already computed samples
    # when the EasyVVUQ grid is refined adaptively.
    if int(skip) > 0:
        # all runs in the campaign dir
        runs = os.listdir("{}/runs/".format(campaign_dir))

        for run in runs:
            # extract X from run_X
            run_id = int(run.split("_")[-1])
            # if X > skip, copy run directory to the sweep dir
            if run_id > int(skip):
                print("Copying {}".format(run))
                local("rsync -pthrz {}/runs/{} {}".format(
                    campaign_dir, run, sweep_dir
                    )
                )
    # if skip = 0: copy all runs from EasyVVUQ run directory to the sweep dir
    else:
        local("rsync -pthrz {}/runs/ {}".format(campaign_dir, sweep_dir))
        

def prepare_job_locally(item, replica, config_dir, sweep_dir, results_base, script_template_name, item_index):
    # Create target directory: RUNS/run_{item_index}_{replica}
    job_folder = Path(results_base) / script_template_name / "RUNS" / f"run_{item_index}_{replica}"
    job_folder.mkdir(parents=True, exist_ok=True)

    # Copy config files (excluding SWEEP)
    for file in Path(config_dir).glob("*"):
        if file.name != "SWEEP":
            dest = job_folder / file.name
            if file.is_dir():
                shutil.copytree(file, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(file, dest)

    # Copy sweep input files
    sweep_item_dir = Path(sweep_dir) / item
    for file in sweep_item_dir.glob("*"):
        dest = job_folder / file.name
        if file.is_dir():
            shutil.copytree(file, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(file, dest)

    # Generate job script
    script_basename = f"{script_template_name}_{item_index}_{replica}.sh"
    job_script_path = job_folder / script_basename

    # Set env variables needed for template rendering
    env.label = f"{item}_replica_{replica}" if replica > 1 else item
    env.job_results = str(job_folder)

    # Locate templates
    header_path = next(
        (Path(p) / env.batch_header for p in env.local_templates_path if (Path(p) / env.batch_header).exists()),
        None
    )
    script_path = next(
        (Path(p) / env.script for p in env.local_templates_path if (Path(p) / env.script).exists()),
        None
    )

    if header_path is None or script_path is None:
        raise FileNotFoundError("Could not locate header or script template.")
    
    # Set remote path for job (used in script templates)
    env.job_results = str(
        Path(env.results_path) / script_template_name / "RUNS" / f"run_{item_index}_{replica}"
    )
    
    # Keep local path for rsync
    env.job_results_local = str(job_folder)
    
    # Read and combine template content
    header = header_path.read_text()
    body = template(script_path.read_text())
    script_content = header + body

    # Write script to file
    with open(job_script_path, "w") as f:
        f.write(script_content)
        
    os.chmod(job_script_path, 0o755)
    
    # Return path to generated script
    return str(job_script_path)

        
@beartype
def run_ensemble(
    config: str,
    sweep_dir: str,
    sweep_on_remote: Optional[bool] = False,
    execute_put_configs: Optional[bool] = True,
    upsample: str = "",
    replica_start_number: str = "1",
    **args,
) -> None:
    """
    Map and execute ensemble jobs.
    Handles both local and remote (PilotJob) execution.

    Args:
        config (str): Name of the base config directory.
        sweep_dir (str): Path to the SWEEP directory (local or remote).
        sweep_on_remote (bool): True if SWEEP dir is on the remote system.
        execute_put_configs (bool): True to run put_configs().
        upsample (str): Optional semicolon-separated list of sweep items.
        replica_start_number (str): Replica start index (or count).
        **args: Additional command-line arguments from user.
    """
    update_environment(args)
    print(f"[DEBUG] run_ensemble called with config={config}")
    print(f"[DEBUG] run_ensemble called with sweep_dir={sweep_dir}")
    
    if not sweep_on_remote:
        print("[INFO] There are no SWEEP directory on Remote machine (sweep_on_remote=False)")

    if "script" not in env:
        raise RuntimeError("ERROR: 'script' must be specified in the environment.")
    
    if not hasattr(env, "job_config_path"):
        raise RuntimeError("with_config() must be called before run_ensemble()")
    
    # Set up PilotJob environment if needed
    if hasattr(env, "PJ") and env.PJ.lower() == "true":
        env.submitted_jobs_list = []
        env.submit_job = False
        env.batch_header = "bash_header"
    
    # Always expect to work from a local SWEEP directory
    if not os.path.exists(sweep_dir):
        raise RuntimeError(f"ERROR: sweep directory '{sweep_dir}' doesn't exist")

    # Normalize sweepdir_items from local directory
    sweepdir_items_all = [
        f for f in os.listdir(sweep_dir)
        if os.path.isdir(os.path.join(sweep_dir, f))
    ]

    if not sweepdir_items_all:
        raise RuntimeError(f"[ERROR] No valid directories found in sweep_dir: {sweep_dir}")

    # Determine upsample list
    upsample_items = [item.strip() for item in upsample.split(";")] if upsample else []
    replica_counts_raw = replica_start_number.strip()

    # Handle replica logic
    if upsample_items:
        # Case: user specified upsample + replica_start_number
        if ";" in replica_counts_raw:
            replica_counts = [int(x.strip()) for x in replica_counts_raw.split(";")]
        else:
            raise RuntimeError(
                f"[ERROR] You specified {len(upsample_items)} upsample items "
                f"but provided only one replica count.\n"
                "Please provide matching replica counts, e.g.: "
                'replica_start_number="2;2" for upsample="d1;d2"'
            )

        if len(replica_counts) != len(upsample_items):
            raise RuntimeError(
                f"[ERROR] Mismatch between sweepdir_items and replica_counts.\n"
                f"Items ({len(upsample_items)}): {upsample_items}\n"
                f"Counts ({len(replica_counts)}): {replica_counts}\n"
                f"Each item in upsample must have exactly one replica count."
            )

        sweepdir_items = upsample_items
    else:
        # Default mode: use all local sweep items, 1 replica each
        sweepdir_items = sweepdir_items_all
        replica_counts = [1] * len(sweepdir_items)
    
    # Creating directory for job dirs and scripts
    if env.job_name_template_sh.endswith(".sh"):
        env.job_name_template = env.job_name_template_sh[:-3]
    else:
        env.job_name_template = env.job_name_template_sh
        
    if not hasattr(env, "tmp_work_path"):
        env.tmp_work_path = Path(tempfile.mkdtemp()) / "FabSim3"

    env.tmp_results_path = env.tmp_work_path / "results"
    env.tmp_results_path.mkdir(parents=True, exist_ok=True)
    
    item_index_map = {item: idx + 1 for idx, item in enumerate(sweepdir_items)}
    
    # Generate job scripts
    job_scripts_to_submit = []

    for item, count in zip(sweepdir_items, replica_counts):
        for replica in range(1, count + 1):
            script_path = prepare_job_locally(
                item=item,
                replica=replica,
                config_dir=env.job_config_path,
                sweep_dir=sweep_dir,
                results_base=env.tmp_results_path,
                script_template_name=env.job_name_template,
                item_index=item_index_map[item],
            )
            job_scripts_to_submit.append(script_path)

    rich_print(
        f"[INFO] Prepared {len(job_scripts_to_submit)} job scripts in {env.tmp_results_path}"
    )
    
    # Create jobs according to the PJ_TYPE
    # Create jobs according to the PilotJob type
    pj_type = getattr(env, "PJ_TYPE", "").lower()

    if pj_type:
        rich_print(f"[INFO] Using PilotJob mode: {pj_type}")

        pj_dispatch = {
            "rp": run_radical,
            "qcg": run_qcg,
        }

        pilot_job_fn = pj_dispatch.get(pj_type)
        if pilot_job_fn:
            pilot_job_fn(job_scripts_to_submit, env.get("venv", False))
        else:
            raise RuntimeError(f"[ERROR] Unsupported PJ_TYPE '{pj_type}'. Supported types are: {', '.join(pj_dispatch.keys())}")

    rich_print("[INFO] Ensemble submission complete")


def run_radical(job_scripts_to_submit: list, venv="False"):
    rich_print(
        Panel.fit(
            "NOW, we are submitting RADICAL-Pilot Jobs",
            title="[orange_red1]PJ job submission phase[/orange_red1]",
            border_style="orange_red1",
        )
    )

    # Set task model to default
    if not hasattr(env, "task_model"):
        env.task_model = "default"

    # Create a temprary working directory for Radical runtime files
    local_working_dir = path.join(
        env.tmp_results_path, "radical_{}_{}_{}".format(
            env.config, env.machine_name, env.cores
        )
    )
    remote_working_dir = path.join(
        env.results_path, "radical_{}_{}_{}".format(
            env.config, env.machine_name, env.cores
        )
    )
    os.makedirs(local_working_dir, exist_ok=True)

    # Prepare the environment for Radical TaskDescription
    task_descriptions = []
    for index, task_script in enumerate(job_scripts_to_submit, start=1):
        env.update(
            {
                "task_name": f"{env.get('task_name_prefix', 'task')}.{index}",
                "executable": task_script,
            }
        )
        task_descriptions.append(task_script)

    # Prepare the environment for Radical pd_init
    env.update(
        {
            "task_descriptions": task_descriptions,
            "sandbox": remote_working_dir,
        }
    )

    # Locate and copy the radical resources script to the sandbox directory
    radical_resources_content = script_template_content("radical-resources")
    sandbox_resources_path = path.join(
        local_working_dir, ".radical", "pilot", "configs"
    )
    os.makedirs(sandbox_resources_path, exist_ok=True)
    with open(
        path.join(sandbox_resources_path, "resource_fabsim.json"), "w"
    ) as f:
        f.write(radical_resources_content)

    # Generate the radical-PJ-py script using the template
    radical_script_content = script_template_content("radical-PJ-py")
    radical_script_name = "{}_{}_{}_radical.py".format(
        env.config, env.machine_name, env.cores
    )
    radical_local_script_path = path.join(
        local_working_dir, radical_script_name
    )
    radical_remote_script_path = path.join(
        remote_working_dir, radical_script_name
    )

    # Create a temporary local file with the radical script content
    with open(radical_local_script_path, "w") as f:
        f.write(radical_script_content)

    # Transfer Radical configuration script to remote machine
    local(
        template(
            "rsync -pthrvz {}/ $username@$remote:{}/".format(
                local_working_dir, remote_working_dir
            )
        )
    )

    # Construct the run_Radical_PilotJob command
    RP_CMD = []
    if hasattr(env, "venv") and str(env.venv).lower() == "true":
        RP_CMD.append("# Activate the virtual environment")
        RP_CMD.append(f"source {env.virtual_env_path}/bin/activate\n")

    RP_CMD.append("# Check if Job is installed")
    RP_CMD.append(
        "python3 -c 'import radical.pilot' 2>/dev/null || "
        "pip3 install --upgrade radical.pilot\n"
    )
    RP_CMD.append("# Python command for task submission")
    RP_CMD.append(f"python3 {radical_remote_script_path}\n")

    env.run_Radical_PilotJob = "\n".join(RP_CMD)

    # Avoid apply replicas functionality on PilotJob folders
    env.replicas = "1"
    backup_header = env.batch_header
    env.batch_header = env.radical_PJ_header
    env.submit_job = True

    job(dict(ensemble_mode=False, label="radical-PJ-header", NoEnvScript=True))
    env.batch_header = backup_header
    env.NoEnvScript = False
    

def run_qcg(job_scripts_to_submit: list, venv: bool):
    """Prepare and submit a QCG-PilotJob using FabSim-style templates."""

    if not job_scripts_to_submit:
        rich_print("[red]Error: No job scripts to submit[/red]")
        return

    rich_print(Panel.fit(
        f"Preparing QCG-PilotJob submission for {len(job_scripts_to_submit)} tasks",
        title="[orange_red1]QCG-PJ Submission[/orange_red1]",
        border_style="orange_red1",
    ))

    # Define run name and paths
    run_name = env.job_name_template
    tmp_results_path = Path(env.tmp_results_path) / run_name
    qcg_dir_local = tmp_results_path / "QCG"
    qcg_dir_local.mkdir(parents=True, exist_ok=True)
    env.qcg_dir_remote = Path(env.results_path) / run_name / "QCG"
    
    # Remote run name and path
    results_path = Path(env.results_path) / run_name
    
    print(f"qcg_dir: {qcg_dir_local}")
    print(f"tmp_results_path: {tmp_results_path}")
    print(f"results_path: {results_path}")

    # -------------------------------
    # 1. Generate JOB_DESCRIPTIONS
    # -------------------------------
    rich_print("[INFO] Creating task descriptions...")
    
    task_blocks = []
    for index, job_script in enumerate(job_scripts_to_submit, start=1):
        env.idsID = index
        rel_path = Path(job_script).relative_to(env.tmp_results_path)
        remote_path = Path(env.results_path) / rel_path
        env.idsPath = str(remote_path)
        env.dirPath = str(remote_path.parent)
        env.cores =  env.cores
        env.task_model = getattr(env, "task_model", "default")
        # Generate script content from template
        script_content = script_template_content("qcg-PJ-task-template")
        task_blocks.append(script_content)
        
    rich_print(f"[INFO] Created {len(task_blocks)} task descriptions.")

    env.JOB_DESCRIPTIONS = textwrap.indent("\n".join(task_blocks), "    ")

    # -------------------------------
    # 2. Generate QCG Python Manager Script
    # -------------------------------
    env.qcg_python_script_local = str(qcg_dir_local / f"qcg_manager_{run_name}.py")
    env.qcg_python_script = str(Path(env.qcg_dir_remote) / f"qcg_manager_{run_name}.py")
    
    print("env.qcg_python_script_local", env.qcg_python_script_local)
    print("env.qcg_python_script", env.qcg_python_script)

    python_script = script_template_content("qcg-PJ-py")
    with open(env.qcg_python_script_local, "w") as f:
        f.write(python_script)
    os.chmod(env.qcg_python_script_local, 0o755)

    # -------------------------------
    # 3. Generate Submission Wrapper Script
    # -------------------------------
    env.qcg_submit_script_local = str(qcg_dir_local / f"qcg_submit_{run_name}.sh")
    env.qcg_submit_script = str(Path(env.qcg_dir_remote) / f"qcg_submit_{run_name}.sh")
    
    print("env.qcg_submit_script_local", env.qcg_submit_script_local)
    print("env.qcg_submit_script", env.qcg_submit_script)
    
    env.batch_header = env.PJ_header
    env.submit_job = True
    
    # -------------------------------
    # 4. Transfer & Submit
    # -------------------------------
    # Create run_QCG_PilotJob command
    PJ_CMD = []
    PJ_CMD.append("# Run the QCG manager script")
    PJ_CMD.append(f"python3 {env.qcg_python_script}")

    # Store in env for SLURM template
    env.run_QCG_PilotJob = "\n".join(PJ_CMD)

    # Temprarily create a job_results directory (X)
    env.job_results = env.qcg_dir_remote
    
    print("env.job_results", env.job_results)
    
    # Write the submission wrapper script (always render with template)
    with open(env.qcg_submit_script_local, "w") as f:
        # HPC: use the full SLURM template, also render with template
        submit_script_content = script_template_content("archer2-PJ-header")
        rendered_submit_script = template(submit_script_content)
        f.write(rendered_submit_script)
            
    os.chmod(env.qcg_submit_script_local, 0o755)
    
    # Create the QCG directory on the remote machine
    run(f"mkdir -p {env.results_path}")
    
    rsync_project(
        local_dir=str(tmp_results_path), 
        remote_dir=str(results_path)
    )
    
    qcg_job = job_submission(dict(job_script=env.qcg_submit_script))
    
    return qcg_job


@task
def install_packages(venv: bool = "False"):
    """
    Install list of packages defined in deploy/applications.yml

    !!! note
        if you got an error on your local machine during the build wheel
        for scipy, like this one
            ```sh
            ERROR: lapack_opt_info:
            ```
        Try to install BLAS and LAPACK first. by
            ```sh
            sudo apt-get install libblas-dev
            sudo apt-get install liblapack-dev
            sudo apt-get install libatlas-base-dev
            sudo apt-get install gfortran
            ```

    Args:
        venv (str, optional): `True` means the VirtualEnv is already installed
            in the remote machine
    """
    applications_yml_file = os.path.join(
        env.fabsim_root, "deploy", "applications.yml"
    )
    user_applications_yml_file = os.path.join(
        env.fabsim_root, "deploy", "applications_user.yml"
    )
    if not os.path.exists(user_applications_yml_file):
        copyfile(applications_yml_file, user_applications_yml_file)

    config = yaml.load(
        open(user_applications_yml_file), Loader=yaml.SafeLoader
    )

    tmp_app_dir = "{}/tmp_app".format(env.localroot)
    local("mkdir -p {}".format(tmp_app_dir))

    for dep in config["packages"]:
        local("pip3 download --no-binary=:all: -d {} {}".format(
                tmp_app_dir, dep
            )
        )
    add_dep_list_compressed = sorted(
        Path(tmp_app_dir).iterdir(), key=lambda f: f.stat().st_mtime
    )
    for it in range(len(add_dep_list_compressed)):
        add_dep_list_compressed[it] = os.path.basename(
            add_dep_list_compressed[it]
        )

    # Create  directory in the remote machine to store dependency packages
    run(template("mkdir -p {}".format(env.app_repository)))

    # Send the dependencies (and the dependencies of dependencies) to the
    # remote machine
    for whl in os.listdir(tmp_app_dir):
        local(
            template(
                "rsync -pthrvz -e 'ssh -p $port'  {}/{} "
                "$username@$remote:$app_repository".format(tmp_app_dir, whl)
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
        if venv.lower() == "true":
            sc.write(
                "if [ ! -d {} ]; then \n\t python -m virtualenv "
                "{} || echo 'WARNING : virtualenv is not installed "
                "or has a problem' \nfi\n\nsource {}/bin/activate\n".format(
                    env.virtual_env_path,
                    env.virtual_env_path,
                    env.virtual_env_path,
                )
            )
            install_dir = ""

        # First install the additional_dependencies
        for dep in reversed(add_dep_list_compressed):
            print(dep)
            if dep.endswith(".zip"):
                sc.write(
                    "\nunzip {}/{} -d {} && cd {}/{} "
                    "&& python3 setup.py install {}".format(
                        env.app_repository,
                        dep,
                        env.app_repository,
                        env.app_repository,
                        dep.replace(".zip", ""),
                        install_dir,
                    )
                )
            elif dep.endswith(".tar.gz"):
                sc.write(
                    "\ntar xf {}/{} -C {} && cd {}/{} "
                    "&& python3 setup.py install {}\n".format(
                        env.app_repository,
                        dep,
                        env.app_repository,
                        env.app_repository,
                        dep.replace(".tar.gz", ""),
                        env.virtual_env_path,
                        install_dir,
                    )
                )

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

    env.job_dispatch += " -q standard"

    print(env.job_dispatch)
    print(env.dest_name)

    run(template("{} {}".format(env.job_dispatch, env.dest_name)))

    local("rm -rf {}".format(tmp_app_dir))


@task
def install_app(name="", external_connexion="no", venv="False"):
    """
    Install a specific Application through FasbSim3

    """
    applications_yml_file = os.path.join(
        env.fabsim_root, "deploy", "applications.yml"
    )
    user_applications_yml_file = os.path.join(
        env.fabsim_root, "deploy", "applications_user.yml"
    )
    if not os.path.exists(user_applications_yml_file):
        copyfile(applications_yml_file, user_applications_yml_file)

    config = yaml.load(
        open(user_applications_yml_file), Loader=yaml.SafeLoader
    )
    info = config[name]

    # Offline cluster installation - --user install
    # Temporary folder
    tmp_app_dir = "{}/tmp_app".format(env.localroot)
    local("mkdir -p {}".format(tmp_app_dir))

    # First download all the Miniconda3 installation script
    local(
        "wget {} -O {}/miniconda.sh".format(
            config["Miniconda-installer"]["repository"], tmp_app_dir
        )
    )

    # Install app-specific requirements

    if name == "RADICAL-Pilot":
        local("pip3 install radical.pilot")

    if name == "QCG-PilotJob":
        local("pip3 install -r " + env.localroot + "/qcg_requirements.txt")

    # Next download all the additional dependencies
    for dep in info["additional_dependencies"]:
        local("pip3 download --no-binary=:all: -d {} {}".format(
            tmp_app_dir, dep
            )
        )
    add_dep_list_compressed = sorted(
        Path(tmp_app_dir).iterdir(), key=lambda f: f.stat().st_mtime
    )
    for it in range(len(add_dep_list_compressed)):
        add_dep_list_compressed[it] = os.path.basename(
            add_dep_list_compressed[it]
        )

    # Download all the dependencies of the application
    # This first method should download all the dependencies needed
    # but for the local plateform !
    # --> Possible Issue during the installation in the remote
    # (it's not a cross-plateform install yet)
    local(
        "pip3 download --no-binary=:all: -d {} git+{}@v{}".format(
            tmp_app_dir, info["repository"], info["version"]
        )
    )

    # Create  directory in the remote machine to store dependency packages
    run(template("mkdir -p {}".format(env.app_repository)))
    # Send the dependencies (and the dependencies of dependencies) to the
    # remote machine
    for whl in os.listdir(tmp_app_dir):
        local(
            template(
                "rsync -pthrvz -e 'ssh -p $port'  {}/{} "
                "$username@$remote:$app_repository".format(tmp_app_dir, whl)
            )
        )

    # Set required env variable
    env.config = "Install_VECMA_App"
    # env.nodes = 1
    env.nodes = env.cores
    script = os.path.join(tmp_app_dir, "script")
    # Write the Install command in a file
    with open(script, "w") as sc:
        install_dir = ""
        if venv == "True":
            # clean virtualenv and App_repo directory on remote machine side
            # To make sure everything is going to be installed from scratch
            """
            sc.write("find %s/ -maxdepth 1 -mindepth 1 -type d \
                -exec rm -rf \"{}\" \\;\n" % (env.app_repository))
            sc.write("rm -rf %s\n" % (env.virtual_env_path))
            """

            # It seems some version of python/virtualenv doesn't support
            # the option --no-download. So there is sometime a problem :
            # from pip import main
            # ImportError: cannot import name 'main'
            #
            # TODO Check python version and raised a Warning if not the
            # right version ?
            # TODO
            #
            sc.write(
                "if [ ! -d {} ]; then \n\t bash {}/miniconda.sh -b -p {} "
                "|| echo 'WARNING : virtualenv is not installed "
                "or has a problem' \nfi".format(
                    env.virtual_env_path,
                    env.app_repository,
                    env.virtual_env_path,
                )
            )
            sc.write(
                '\n\neval "$$({}/bin/conda shell.bash hook)"\n\n'.format(
                    env.virtual_env_path
                )
            )
            # install_dir = ""
            """
            with the latest version of numpy, I got this error:
            1. Check that you expected to use Python3.8 from ...,
                and that you have no directories in your PATH or PYTHONPATH
                that can interfere with the Python and numpy version "1.18.1"
                you're trying to use.
            so, since that we are using VirtualEnv, to avoid any conflict,
            it is better to clear PYTHONPATH
            """
            # sc.write("\nexport PYTHONPATH=\"\"\n")
            sc.write("\nmodule unload python\n")

        # First install the additional_dependencies
        for dep in reversed(add_dep_list_compressed):
            print(dep)
            if dep.endswith(".zip"):
                sc.write(
                    "\nunzip {}/{} -d {} && cd {}/{} "
                    "&& {}/bin/python3 setup.py install {}\n".format(
                        env.app_repository,
                        dep,
                        env.app_repository,
                        env.app_repository,
                        dep.replace(".zip", ""),
                        env.virtual_env_path,
                        install_dir,
                    )
                )
            elif dep.endswith(".tar.gz"):
                sc.write(
                    "\ntar xf {}/{} -C {} && cd {}/{} "
                    "&& {}/bin/python3 setup.py install {}\n".format(
                        env.app_repository,
                        dep,
                        env.app_repository,
                        env.app_repository,
                        dep.replace(".tar.gz", ""),
                        env.virtual_env_path,
                        install_dir,
                    )
                )

        sc.write(
            "{}/bin/pip install --no-index --no-build-isolation "
            "--find-links=file:{} {}/{}-{}.zip {} || "
            "{}/bin/pip install --no-index "
            "--find-links=file:{} {}/{}-{}.zip".format(
                env.virtual_env_path,
                env.app_repository,
                env.app_repository,
                info["name"],
                info["version"],
                install_dir,
                env.virtual_env_path,
                env.app_repository,
                env.app_repository,
                info["name"],
                info["version"],
            )
        )

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

    env.job_dispatch += " -q standard"

    print(env.job_dispatch)
    print(env.dest_name)

    run(template("{} {}".format(env.job_dispatch, env.dest_name)))

    local("rm -rf {}".format(tmp_app_dir))


def count_folders(dir_path: str, prefix: str):
    """
    Count the number of folders in a path that match a pattern
    """
    dirs = os.listdir(dir_path)
    return len([d for d in dirs if d.startswith(prefix)])
