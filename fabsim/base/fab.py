import math
import os
import re
import subprocess
import tempfile
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
        name (str): the name of plugin

    Returns:
        str: the path of plugin

    Raises:
        RuntimeError: if the requested plugin is not installed in the
            local system
    """
    plugin_path = os.path.join(env.localroot, "plugins", name)
    if not os.path.exists(plugin_path):
        raise RuntimeError(f"Plugin {name} is not installed.")
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
        name (str): the name of results directory
    """
    with_job(name)
    run(template("mkdir -p $job_results"))
    if env.manual_gsissh:
        local(template("globus-url-copy -cd -r -sync $job_results_local/ gsiftp://$remote/$job_results/"))
    else:
        rsync_project(local_dir=env.job_results_local + "/", remote_dir=env.job_results)


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
    includes_files = " ".join([f"--include='{file}'" for file in fetch_files])

    env.job_results, env.job_results_local = with_job(name)

    # check if the local results directory exists or not
    if not os.path.isdir(env.job_results_local):
        os.makedirs(env.job_results_local)

    if env.manual_sshpass:
        local(template(f"rsync -pthrvz {includes_files} $username@$remote:$job_results/ $job_results_local/"))
    elif env.manual_gsissh:
        local(template(f"globus-url-copy -cd -r -sync gsiftp://$remote/$job_results/ file://$job_results_local/"))
    else:
        rsync_project(local_dir=env.job_results_local + "/", remote_dir=env.job_results)


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
            "function can not be found !!!").format(task)
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
        # scp a monsoonfab:~/ ; ssh monsoonfab -C "scp ~/a xcscfab:~/"
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
    - `job_results_local`: the local location where job results should
          be stored


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
        
    print(f"job args: {args}")

    # check if with_config function is already called or not
    if not hasattr(env, "job_config_path"):
        raise RuntimeError(
            "Function with_config did NOT called, "
            "Please call it before calling job()"
        )

    update_environment(args)
    
    # Add label, mem, core to env.
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
                    sweepdir_items=env.sweepdir_items,
                ),
            )
    else:
        args["replica_start_number"] = env.replica_start_number
        POOL.add_task(func=job_preparation, func_args=args)

    print("Submit tasks to multiprocessingPool : done ...")
    job_scripts_to_submit = POOL.wait_for_tasks()

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
    
    if prepare_only:
        return job_scripts_to_submit

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
    Prepare job folders and scripts in the temporary folder.
    """
    pprint(f"job preparation args: {job_args}")

    args = {}
    for adict in job_args:
        args = dict(args, **adict)

    update_environment(args)

    if "label" in args:
        env.label = args["label"]
    else:
        env.label = ""

    return_job_scripts = []

    print(f"sweepdir_items: {env.sweepdir_items}")
    print("We are in job preparation phase")

    # Use preprocessed sweepdir_items and replica_start_number from run_ensemble
    for i, sweep_item in enumerate(env.sweepdir_items):
        # Ensure replica_start_number is always a list
        replica_start_number = args.get("replica_start_number", [1] * len(args["sweepdir_items"]))
        if isinstance(replica_start_number, int):
            replica_start_number = [replica_start_number] * len(args["sweepdir_items"])

        replica_start = replica_start_number[i]
        replica_count = replica_start + 1  # Adjusted to include the starting replica

        for replica_index in range(replica_start, replica_count):
            env.replica_number = replica_index

            env.job_results, env.job_results_local = with_template_job(
                ensemble_mode=env.ensemble_mode, label=env.label
            )

            # Create unique directories for each replica
            env.job_results = os.path.join(env.job_results, f"replica{replica_index}")
            env.job_results_local = os.path.join(env.job_results_local, f"replica{replica_index}")

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

            tmp_job_script = script_templates(env.batch_header, env.script)

            base, extension = os.path.splitext(env.pather.basename(tmp_job_script))

            dst_script_name = f"{base}_replica{replica_index}{extension}"
            dst_job_script = env.pather.join(env.tmp_scripts_path, dst_script_name)

            return_job_scripts.append(
                env.pather.join(env.job_results, dst_script_name)
            )

            copy(tmp_job_script, dst_job_script)
            os.chmod(dst_job_script, 0o755)

            os.makedirs(tmp_job_results, exist_ok=True)
            copy(dst_job_script, env.pather.join(tmp_job_results, dst_script_name))

            with open(
                env.pather.join(tmp_job_results, "env.yml"), "w"
            ) as env_yml_file:
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

    # Add debugging logs to confirm the return value of job_preparation
    print(f"[DEBUG] job_preparation return value: {return_job_scripts}")

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
            # scp a monsoonfab:~/ ; ssh monsoonfab -C "scp ~/a xcscfab:~/"
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
    Submit all prepared job scripts to the target remote machine.

    Args:
        job_args: Arguments containing job script details.
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
    Convert an ensemble directory into a campaign directory.

    Args:
        results_dir (str): Path to the ensemble results directory.
        campaign_dir (str): Path to the campaign directory.
        skip (Union[int, str], optional): Number of runs to skip. Defaults to 0.
    """
    if int(skip) > 0:
        print(f"Skipping the first {skip} runs.")

    # all run directories
    runs = os.listdir(f"{results_dir}/RUNS/")
    for run in runs:
        src = os.path.join(results_dir, "RUNS", run)
        dst = os.path.join(campaign_dir, run)
        if os.path.isdir(src):
            copy(src, dst)


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
    # if skip = 0: copy all runs from EasyVVUQ run directort to the sweep dir
    else:
        local("rsync -pthrz {}/runs/ {}".format(campaign_dir, sweep_dir))
        
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
    print("\n[DEBUG] run_ensemble called with arguments:")
    print(f"  config                : {config}")
    print(f"  sweep_dir             : {sweep_dir}")
    print(f"  sweep_on_remote       : {sweep_on_remote}")
    print(f"  execute_put_configs   : {execute_put_configs}")
    print(f"  upsample              : {upsample}")
    print(f"  replica_start_number  : {replica_start_number}")
    print(f"  additional env.script : {env.script}")
    print(f"  additional **args     : {args}")
    update_environment(args)
    
    if "script" not in env:
        raise RuntimeError("ERROR: 'script' must be specified in the environment.")
    
    if not hasattr(env, "job_config_path"):
        raise RuntimeError("with_config() must be called before run_ensemble()")
    
    # Set up PilotJob environment if needed
    if hasattr(env, "PJ") and env.PJ.lower() == "true":
        env.submitted_jobs_list = []
        env.submit_job = False
        env.batch_header = "bash_header"
    
    # 1. DETERMINE SWEEP ITEMS
    # ========================
    if sweep_on_remote:
        # Get sweep items from remote directory
        rich_print("[INFO] Reading sweep directory items from remote machine...")
        sweepdir_items = run(f"ls -1 {sweep_dir}").splitlines()
        if not sweepdir_items:
            raise RuntimeError(f"ERROR: No files found in remote sweep_dir: {sweep_dir}")
    else:
        # Read local sweep items
        if not os.path.exists(sweep_dir):
            raise RuntimeError(f"ERROR: sweep directory '{sweep_dir}' doesn't exist")
            
        if len(os.listdir(sweep_dir)) == 0:
            raise RuntimeError(f"ERROR: no files found in the sweep_dir: {sweep_dir}")
            
        # Parse upsample list - if provided, use only those items
        if upsample:
            upsample_items = upsample.split(";")
            # Validate all upsample items exist in sweep directory
            all_items = os.listdir(sweep_dir)
            missing_items = set(upsample_items) - set(all_items)
            if missing_items:
                raise RuntimeError(f"ERROR: Upsample items not found in sweep directory: {missing_items}")
            sweepdir_items = upsample_items
        else:
            # Use all folders in the SWEEP dir
            sweepdir_items = os.listdir(sweep_dir)
    
    rich_print(f"[INFO] Processing {len(sweepdir_items)} sweep items")
    
    # 2. PARSE REPLICA COUNTS
    # =======================
    if ";" in replica_start_number:
        replica_counts = list(map(int, replica_start_number.split(";")))
        if len(replica_counts) != len(sweepdir_items):
            raise RuntimeError("Mismatch between number of sweep items and replica counts.")
    else:
        replica_counts = [int(replica_start_number)] * len(sweepdir_items)
    
    # 3. PRIORITIZE EXECUTION IF NEEDED
    # =================================
    if hasattr(env, "exec_first") and env.exec_first in sweepdir_items:
        rich_print(f"[INFO] Prioritizing execution of '{env.exec_first}'")
        sweepdir_items.insert(0, sweepdir_items.pop(sweepdir_items.index(env.exec_first)))
    
    # Update env to reflect the reordering
    env.sweepdir_items = sweepdir_items
    env.replica_start_number = replica_counts
    
    # 4. TRANSFER CONFIG FILES
    # ========================
    if execute_put_configs:
        rich_print(f"[INFO] Uploading configuration files from '{config}'")
        execute(put_configs, config)
    
    # 5. PREPARE JOB SCRIPTS (local preparation)
    # ==========================================
    rich_print("[INFO] Preparing job scripts...")

    job_scripts_to_submit = job(
        dict(
            ensemble_mode=True,
            sweepdir_items=env.sweepdir_items,
            sweep_dir=sweep_dir,
            replica_start_number=env.replica_start_number,
        ),
        prepare_only=True
    )
    
    rich_print(f"[INFO] Prepared {len(job_scripts_to_submit)} job scripts")
    
    # exit(0)
    
    # Create a consolidated results directory for the run
    # This follows FabSim3 structure better
    folder_name = f"{env.config}_{env.machine_name}_{env.cores}"
    env.run_name = folder_name
    
    # 6. HANDLE SUBMISSION BASED ON PILOT JOB TYPE
    # ===========================================
    if hasattr(env, "PJ_TYPE"):
        pj_type = env.PJ_TYPE.lower()
        rich_print(f"[INFO] Using PilotJob mode: {pj_type}")
        
        if pj_type == "rp":
            run_radical(job_scripts_to_submit, env.get("venv", False))
        elif pj_type == "qcg":
            run_qcg(job_scripts_to_submit, env.get("venv", False))
        else:
            raise RuntimeError(f"ERROR: Unsupported PJ_TYPE '{pj_type}'. Use 'RP' or 'QCG'")
    else:
        # Standard submission - the job function handles the actual submission
        rich_print("[INFO] Submitting jobs through standard scheduler")
        # We use the same parameters as in the prepare step, but without prepare_only
        # This will cause the job function to execute the submission step
        job(
            dict(
                ensemble_mode=True,
                sweepdir_items=env.sweepdir_items,
                sweep_dir=sweep_dir,
                replica_start_number=env.replica_start_number,
            )
        )
    
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
    """
    Create and submit a QCG-PilotJob that will execute all provided job scripts.
    All preparation is done locally, then transferred in a single step before execution.
    
    Args:
        job_scripts_to_submit (list): List of paths to job scripts to be executed
        venv (bool): Whether to use a virtual environment for execution
    """
    rich_print(
        Panel.fit(
            f"Preparing QCG-PilotJob submission for {len(job_scripts_to_submit)} tasks",
            title="[orange_red1]QCG-PJ Submission[/orange_red1]",
            border_style="orange_red1",
        )
    )

    if not job_scripts_to_submit:
        rich_print("[red]Error: No job scripts to submit[/red]")
        return
    
    # Extract the base name of the job from the job script names
    # The path will be something like /tmp/.../results/dummy_test_archer2_4/RUNS/d1/...
    # Or on remote: /work/.../results/dummy_test_archer2_4/RUNS/d1/...
    first_script_path = job_scripts_to_submit[0]
    path_parts = first_script_path.split(os.path.sep)
    
    # Find the results part
    if "results" in path_parts:
        results_index = path_parts.index("results")
        if results_index + 1 < len(path_parts):
            base_name = path_parts[results_index + 1]
        else:
            base_name = f"{env.config}_{env.machine_name}_{env.cores}"
    else:
        base_name = f"{env.config}_{env.machine_name}_{env.cores}"
    
    rich_print(f"[INFO] Base job name: {base_name}")
    
    # Create directories in temporary location for local work
    # These will be transferred later by job_transmission
    temp_dir = env.tmp_work_path if hasattr(env, "tmp_work_path") else tempfile.mkdtemp()
    temp_results_dir = os.path.join(temp_dir, "results", base_name)
    temp_qcg_dir = os.path.join(temp_results_dir, "QCG")
    temp_qcg_logs_dir = os.path.join(temp_qcg_dir, "logs")
    
    os.makedirs(temp_qcg_dir, exist_ok=True)
    os.makedirs(temp_qcg_logs_dir, exist_ok=True)
    
    rich_print(f"[INFO] Created temporary directories for QCG files: {temp_qcg_dir}")
    
    # Set environment variables for remote paths (to be used in templates)
    # These will be used in templates, but we don't create them locally
    remote_results_dir = os.path.join(env.results_path, base_name)
    remote_qcg_dir = os.path.join(remote_results_dir, "QCG")
    remote_qcg_logs_dir = os.path.join(remote_qcg_dir, "logs")
    
    # Store both local and remote paths in env
    env.qcg_dir_local = temp_qcg_dir
    env.qcg_logs_dir_local = temp_qcg_logs_dir
    env.qcg_dir = remote_qcg_dir
    env.qcg_logs_dir = remote_qcg_logs_dir
    env.main_job_dir = remote_results_dir
    
    # Set default task model if not defined
    if not hasattr(env, "task_model"):
        env.task_model = "default"

    # 1. CREATE TASK DESCRIPTIONS 
    # ===========================
    rich_print("[INFO] Creating task descriptions...")
    
    # Create job descriptions directly as a properly formatted string with correct indentation
    job_descriptions = []
    
    for index, job_script in enumerate(job_scripts_to_submit, start=1):
        task_id = f"TaskID{index}"
        script_path = job_script
        directory = path.dirname(script_path)
        
        # Format a single job description with precise indentation (4 spaces)
        job_description = f"""    jobs.add(
        name='{task_id}',
        exec='bash',
        args=['-l', '{script_path}'],
        stdout='{directory}/{task_id}_$' + '{{uniq}}.stdout',
        stderr='{directory}/{task_id}_$' + '{{uniq}}.stderr',
        wd='{directory}',
        numCores={{'exact': {env.cores}}},
        model='{env.task_model}',
    )"""
        job_descriptions.append(job_description)
    
    # Join all job descriptions with newlines
    all_job_descriptions = "\n".join(job_descriptions)
    
    # Store in environment with the new variable name
    env.JOB_DESCRIPTIONS = all_job_descriptions
    
    rich_print(f"[INFO] Created {len(job_descriptions)} task descriptions")
    
    # 2. PREPARE QCG-PJ PYTHON SCRIPT
    # ==============================
    # Avoid applying replicas to PilotJob scripts
    env.replicas = "1"
    
    # Save current header and use PilotJob Python header for generating the script
    backup_header = env.batch_header
    env.batch_header = env.PJ_PYheader
    
    # Set local path for the QCG Python script
    env.qcg_python_script_local = os.path.join(temp_qcg_dir, f"qcg_manager_{base_name}.py")
    # Set remote path for the QCG Python script (for template variables)
    env.qcg_python_script = os.path.join(remote_qcg_dir, f"qcg_manager_{base_name}.py")
    
    rich_print("[INFO] Generating QCG-PilotJob Python script...")
    
    # Use FabSim3's templating directly instead of job() - more efficient
    python_script_content = script_template_content("qcg-PJ-py")
    with open(env.qcg_python_script_local, 'w') as f:
        f.write(python_script_content)
        
    rich_print(f"[INFO] Generated QCG-PJ Python script: {os.path.basename(env.qcg_python_script)}")
    
    # 3. PREPARE SUBMISSION SCRIPT FOR QCG-PJ
    # ======================================
    # Switch to PilotJob header for the batch submission script
    env.batch_header = env.PJ_header
    env.submit_job = True
    
    # Set local path for the QCG submission script
    env.qcg_submit_script_local = os.path.join(temp_qcg_dir, f"qcg_submit_{base_name}.sh")
    # Set remote path for the QCG submission script (for job_submission)
    env.qcg_submit_script = os.path.join(remote_qcg_dir, f"qcg_submit_{base_name}.sh")
    
    # Explicitly set working directories to avoid home dir issues
    env.qcg_work_dir = remote_results_dir 
    env.job_results = remote_results_dir  # Override for template variables
    rich_print(f"[INFO] Setting QCG-PilotJob working directory to: {env.qcg_work_dir}")

    # Pass venv parameters as template variables
    if venv:
        env.venv = "true"
        if hasattr(env, "virtual_env_path"):
            rich_print(f"[INFO] Using virtual environment at: {env.virtual_env_path}")
            
            # Pre-install QCG-PilotJob in the virtual environment
            try:
                rich_print("[INFO] Pre-installing QCG-PilotJob in the virtual environment...")
                cmd = f"ssh $username@$remote 'source {env.virtual_env_path}/bin/activate && pip install qcg-pilotjob'"
                local(template(cmd))
                rich_print("[INFO] QCG-PilotJob pre-installation complete")
            except Exception as e:
                rich_print(f"[WARNING] Failed to pre-install QCG-PilotJob: {str(e)}")
                rich_print("[WARNING] Job may fail if QCG-PilotJob is not already installed")
        else:
            rich_print("[WARNING] venv=true but no virtual_env_path is defined in machines.yml")
    else:
        env.venv = "false"
        
        # Pre-install QCG-PilotJob in the user's home directory
        try:
            rich_print("[INFO] Pre-installing QCG-PilotJob in user's home directory...")
            cmd = "ssh $username@$remote 'pip install --user qcg-pilotjob'"
            local(template(cmd))
            rich_print("[INFO] QCG-PilotJob pre-installation complete")
        except Exception as e:
            rich_print(f"[WARNING] Failed to pre-install QCG-PilotJob: {str(e)}")
            rich_print("[WARNING] Job may fail if QCG-PilotJob is not already installed")
    
    # Construct the QCG-PilotJob execution command
    PJ_CMD = []
    
    # First create required directories on remote system
    PJ_CMD.append("# Create required directories")
    PJ_CMD.append(f"mkdir -p {remote_qcg_dir}")
    PJ_CMD.append(f"mkdir -p {remote_qcg_logs_dir}")
    PJ_CMD.append("")
    
    # Add directory change and setup
    PJ_CMD.append("# Change to working directory")
    PJ_CMD.append(f"cd {env.qcg_work_dir} || (echo 'Failed to cd to {env.qcg_work_dir}' && exit 1)")
    PJ_CMD.append("pwd") # Debug: print working directory
    PJ_CMD.append("")
    
    # Add virtual environment activation if required
    if hasattr(env, "venv") and str(env.venv).lower() == "true":
        PJ_CMD.append("# Activate the virtual environment")
        PJ_CMD.append("echo 'Activating virtual environment'")
        
        # Handle different types of virtual environments (venv, conda, etc.)
        if hasattr(env, "virtual_env_path"):
            venv_path = env.virtual_env_path
            PJ_CMD.append(f"# Virtual environment path: {venv_path}")
            
            # Check if this is a conda environment
            if os.path.exists(f"{venv_path}/etc/conda"):
                PJ_CMD.append(f"source {venv_path}/etc/profile.d/conda.sh")
                PJ_CMD.append(f"conda activate base")
            # Check if it's a standard venv/virtualenv
            elif os.path.exists(f"{venv_path}/bin/activate"):
                PJ_CMD.append(f"source {venv_path}/bin/activate")
            # Default to bin directory on path (module based approach)
            else:
                PJ_CMD.append(f"export PATH={venv_path}/bin:$PATH")
                PJ_CMD.append(f"export PYTHONPATH={venv_path}/lib/python*/site-packages:$PYTHONPATH")
        else:
            # No specific path, try standard module approach
            PJ_CMD.append("module load python")
        
        PJ_CMD.append("# Print Python information for debugging")
        PJ_CMD.append("which python3")
        PJ_CMD.append("python3 --version")
        PJ_CMD.append("echo \"PYTHONPATH=$PYTHONPATH\"")
        PJ_CMD.append("")

    # Add QCG-PilotJob installation check
    PJ_CMD.append("# Check if QCG-PilotJob is installed")
    if hasattr(env, "venv") and str(env.venv).lower() == "true":
        # In a virtual environment, don't use --user flag
        PJ_CMD.append(
            "python3 -c 'import qcg.pilotjob.api' 2>/dev/null || "
            "pip3 install qcg-pilotjob"
        )
    else:
        # Not in a virtual environment, use --user flag
        PJ_CMD.append(
            "python3 -c 'import qcg.pilotjob.api' 2>/dev/null || "
            "pip3 install --user qcg-pilotjob"
        )
    PJ_CMD.append("pip3 list | grep qcg")
    PJ_CMD.append("")
    
    # Add command to run the Python script
    PJ_CMD.append("# Execute QCG-PilotJob workflow")
    PJ_CMD.append(f"python3 {env.qcg_python_script}")

    # Store command in environment for template use
    env.run_QCG_PilotJob = "\n".join(PJ_CMD)
    
    # Use FabSim3's templating directly for the submission script
    submit_script_content = script_template_content("archer2-PJ-header")
    with open(env.qcg_submit_script_local, 'w') as f:
        f.write(submit_script_content)
    
    # Make the script executable
    os.chmod(env.qcg_submit_script_local, 0o755)
    
    # 4. TRANSFER AND SUBMIT THE QCG-PJ JOB
    # ====================================
    rich_print("[INFO] Transferring QCG-PilotJob files...")
    
    # Make sure these files are included when job_transmission is called
    env.results_to_include = [base_name] 
    
    # Ensure the job transmission includes our QCG files
    # This leverages the existing job_transmission function which is already optimized
    job_transmission()
    
    rich_print("[INFO] Submitting QCG-PilotJob manager job...")
    
    # Submit the QCG job script
    job_submission(dict(job_script=env.qcg_submit_script))
    
    # Restore original batch header
    env.batch_header = backup_header
    env.NoEnvScript = False
    
    rich_print(
        Panel.fit(
            f"QCG-PilotJob submission complete. Job will execute {len(job_scripts_to_submit)} tasks.",
            title="[green]Success[/green]",
            border_style="green",
        )
    )
    
    return env.qcg_submit_script


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
                "$username@$remote:$app_repository".format(
                    tmp_app_dir, whl
                )
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
