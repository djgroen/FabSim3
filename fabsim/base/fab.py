import math
import os
import re
import subprocess
import tempfile
import textwrap
import threading
import time
from pathlib import Path
from pprint import pformat, pprint
from shutil import copy, copyfile, rmtree

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
            f"fabsim localhost install_plugin: {name}"
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
                f"rsync -pthrvz --rsh='sshpass {sshpass_args} ssh -p 22  ' "
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
        ExceptWhenNotFound (bool, optional): if `True`, raise an exception
        when the input config name not found. Defaults to `True`.

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

    if not hasattr(env, "all_job_results"):
        env.all_job_results = []
    if not hasattr(env, "all_job_results_local"):
        env.all_job_results_local = []

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

    # Store all results paths for later use
    env.all_job_results.append(job_results)
    env.all_job_results_local.append(job_results_local)

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


def job(*job_args):
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

    # Show template cache status once per job (main process only)
    from fabsim.deploy.templates import _get_cache_setting
    cache_enabled = _get_cache_setting()
    cache_status = "ENABLED" if cache_enabled else "DISABLED"

    msg = "tmp_work_path = {}\nTemplate cache: {}".format(
        env.tmp_work_path,
        cache_status
    )
    rich_print(
        Panel.fit(
            msg,
            title="[orange_red1]job preparation phase[/orange_red1]",
            border_style="orange_red1",
        )
    )

    print("Submit tasks to multiprocessingPool : start ...")

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

            # Use per-item replica count if available
            if hasattr(
                    env,
                    "replica_counts") and isinstance(
                    env.replica_counts,
                    list):
                replicas = env.replica_counts[index]
            else:
                replicas = env.replicas

            POOL.add_task(
                func=job_preparation,
                func_args=dict(
                    ensemble_mode=env.ensemble_mode,
                    label=task_label,
                    replica_start_number=replica_start_number,
                    replicas=replicas,  # <-- pass as int
                ),
            )
    else:
        args["replica_start_number"] = env.replica_start_number
        args["replicas"] = env.replicas
        POOL.add_task(func=job_preparation, func_args=args)

    print("Submit tasks to multiprocessingPool : done ...")

    def progress_indicator():
        """Display a simple progress bar showing script generation progress."""
        # Calculate total scripts correctly for ensemble/sweep jobs
        total_scripts = 0

        replica_counts_check = (
            hasattr(env, 'replica_counts') and
            isinstance(env.replica_counts, list) and
            len(env.replica_counts) > 0
        )
        if replica_counts_check:
            # For ensemble jobs: sum all replica counts across all
            # upsamples/sweep items
            total_scripts = sum(env.replica_counts)
        elif hasattr(env, 'replicas') and env.replicas:
            # For simple replica jobs: use replicas directly, ensure it's
            # an integer
            try:
                total_scripts = int(env.replicas)
            except (ValueError, TypeError):
                total_scripts = 0
        else:
            # Try to get from environment as fallback
            try:
                total_scripts = int(getattr(env, 'replicas', 0))
            except (ValueError, TypeError):
                total_scripts = 0

        if total_scripts <= 0:
            # Fallback to simple spinner if we don't know the total
            chars = ["|", "/", "-", "\\"]
            count = 0
            while not progress_indicator.done:
                print(
                    f"\rGenerating job scripts... {chars[count % 4]} ",
                    end="",
                    flush=True
                )
                count += 1
                time.sleep(0.5)
            print("\rJob preparation complete!                   ")
            return

        # Progress bar implementation
        last_count = 0
        last_check_time = time.time()
        check_interval = 0.1  # Base check interval

        while not progress_indicator.done:
            current_time = time.time()

            # Dynamic check interval based on total scripts to reduce overhead
            if total_scripts > 500:
                check_interval = 0.5  # Slower updates for large jobs
            elif total_scripts > 100:
                check_interval = 0.3
            else:
                check_interval = 0.1  # Fast updates for small jobs

            # Only check file count if enough time has passed
            if current_time - last_check_time >= check_interval:
                last_check_time = current_time
                current_scripts = 0

                try:
                    script_path_exists = (
                        hasattr(env, 'tmp_scripts_path') and
                        os.path.exists(env.tmp_scripts_path)
                    )
                    if script_path_exists:
                        # Optimized counting: use glob for better performance
                        # with large directories
                        import glob
                        script_pattern = os.path.join(env.tmp_scripts_path,
                                                      "*.sh")
                        current_scripts = len(glob.glob(script_pattern))
                except Exception:
                    current_scripts = last_count

                # Only update display if count changed significantly or at
                # completion
                count_diff = current_scripts - last_count
                completion_check = (
                    current_scripts == total_scripts and
                    last_count != total_scripts
                )

                # Smooth progress bar updates based on percentage milestones
                # and time intervals for a more natural feel
                current_percentage = (
                    (current_scripts / max(1, total_scripts)) * 100
                )
                last_percentage = (last_count / max(1, total_scripts)) * 100

                # Update on meaningful percentage increases or time
                percentage_diff = current_percentage - last_percentage
                min_time_update = 0.5  # Force update every 500ms minimum
                time_since_last_update = (
                    current_time - getattr(progress_indicator,
                                           'last_update_time', 0)
                )

                should_update = (
                    count_diff > 0 and (
                        percentage_diff >= 1.0 or  # Every 1% smooth progress
                        time_since_last_update >= min_time_update or  # Time
                        completion_check or
                        current_scripts == total_scripts
                    )
                )

                if should_update:
                    progress_indicator.last_update_time = current_time
                    last_count = current_scripts
                    percentage = min(100,
                                     (current_scripts / total_scripts) * 100)

                    # Simple progress bar: [####    ] 4/10 (40%)
                    bar_width = 20
                    filled = int(bar_width * current_scripts / total_scripts)
                    bar = '█' * filled + '░' * (bar_width - filled)

                    print(f"\rGenerating scripts: [{bar}] "
                          f"{current_scripts}/{total_scripts} "
                          f"({percentage:.0f}%)",
                          end="", flush=True)

            time.sleep(0.05)  # Sleep to prevent excessive CPU usage

        # Final update
        final_bar = '█' * 20
        print(f"\rScript generation complete: [{final_bar}] "
              f"{total_scripts}/{total_scripts} (100%)           ")
        print()  # Add a newline

    progress_indicator.done = False
    indicator_thread = threading.Thread(target=progress_indicator)
    indicator_thread.daemon = True
    indicator_thread.start()

    # Processing nested job scripts
    try:
        job_scripts_nested = POOL.wait_for_tasks()
    finally:
        # Ensure we always stop the progress indicator
        progress_indicator.done = True
        indicator_thread.join()

    job_scripts_to_submit = []
    job_script_info = {}
    for sublist in job_scripts_nested:
        for item in (sublist if isinstance(sublist, list) else [sublist]):
            if isinstance(item, tuple) and len(item) == 2:
                script_path, info = item
                job_scripts_to_submit.append(script_path)
                job_script_info[script_path] = info
            else:
                job_scripts_to_submit.append(item)
    env.job_scripts_to_submit = job_scripts_to_submit
    env.job_script_info = job_script_info

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

    if not (hasattr(env, "submit_job") and env.submit_job is False):
        # submit jobs
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
    Prepare all job folders and scripts in a temporary directory:
        `<tmp_folder>/{results,scripts}`.
    These files and folders are later transferred in bulk using a
    single `rsync` command during job_transmission.
    This reduces the number of SSH connections and improves the reliability of
    the job submission workflow, especially under high parallelism.
    """
    args = {}
    for adict in job_args:
        args = dict(args, **adict)

    if not hasattr(env, "job_script_info"):
        env.job_script_info = {}

    if "label" in args:
        env.label = args["label"]
    else:
        env.label = ""

    return_job_scripts = []

    for i in range(
        args["replica_start_number"],
        int(args["replicas"]) + args["replica_start_number"],
    ):
        env.replica_number = i

        env.job_results, env.job_results_local = with_template_job(
            ensemble_mode=env.ensemble_mode, label=env.label
        )

        if int(args["replicas"]) > 1:
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

        # Handle PilotJob vs Traditional job script generation
        if hasattr(env, "pj_type"):
            # PilotJob mode: Different logic for headers vs task scripts
            if hasattr(env, "NoEnvScript") and env.NoEnvScript:
                # This is a PilotJob header script (qcg-PJ-header)
                # These DO need SLURM headers since they're the main scripts
                tmp_job_script = script_templates(env.batch_header)
            else:
                # This is a PilotJob task script
                # These should NOT have SLURM headers
                tmp_job_script = script_templates("bash_header", env.script)
        else:
            # Traditional FabSim3 mode: All scripts get SLURM headers
            if hasattr(env, "NoEnvScript") and env.NoEnvScript:
                tmp_job_script = script_templates(env.batch_header)
            else:
                tmp_job_script = script_templates(env.batch_header, env.script)

        # Separate base from extension
        base, extension = os.path.splitext(env.pather.basename(tmp_job_script))
        # Initial new name if we have replicas or ensemble

        if int(args["replicas"]) > 1:
            if env.ensemble_mode is False:
                dst_script_name = base + "_replica_" + str(i) + extension
            else:
                dst_script_name = base + "_" + str(i) + extension
        else:
            dst_script_name = base + extension

        dst_job_script = env.pather.join(env.tmp_scripts_path, dst_script_name)

        # Add target job script to return list (safe mode)
        if hasattr(env, "pj_type"):
            script_path = env.pather.join(env.scripts_path, dst_script_name)
        else:
            script_path = env.pather.join(env.job_results, dst_script_name)
        return_job_scripts.append((script_path, (env.label, str(i))))

        # Store mapping for QCG/RADICAL
        env.job_script_info[script_path] = (env.label, str(i))

        copy(tmp_job_script, dst_job_script)
        # chmod +x dst_job_script
        # 755 means read and execute access for everyone and also
        # write access for the owner of the file
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
                    f"--rsh='sshpass {sshpass_args} ssh -p 22  ' "
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


@beartype
def run_ensemble(
    config: str,
    sweep_dir: str,
    sweep_on_remote: Optional[bool] = False,
    execute_put_configs: Optional[bool] = True,
    upsample: str = "",
    replica_start_number: str = "1",
    **args,
):
    """
    Launch and manage ensemble jobs, mapping each input in the
    sweep directory to a job execution.
    Results are stored according to the environment's naming conventions.

    Note:
        The `with_config` function must be called before
        invoking this function in plugin code.

    Args:
        config (str): Name of the base configuration directory for input files.
        sweep_dir (str): Directory containing per-instance
        input folders for the ensemble.
        sweep_on_remote (bool, optional): If True, the `SWEEP` directory
        is on the remote machine.
        execute_put_configs (bool, optional): If True, configuration files
        have already been transferred.
        **args: Additional keyword arguments for job configuration.
        upsample (str, optional): A semicolon-separated list of
        upsample items to be used (e.g., "item1;item2;item3").
        replica_start_number (str, optional): The starting number for
        the replica count. Defaults to "1".
        replicas (int, optional): The number of replicas to be used.
        If not set, the number of replicas is determined by the
        `replica_counts` list (e.g., [3, 2, 1]) or an integer value.

    Raises:
        RuntimeError: If `with_config` was not called, `env.script` is unset,
        or the sweep directory is empty.
    """
    update_environment(args)

    if "script" not in env:
        raise RuntimeError(
            "[ERROR] run_ensemble function has been called,"
            "but the parameter 'script' was not specified."
        )

    if not config:
        raise RuntimeError(
            "[ERROR] run_ensemble function has been called, "
            "but the parameter 'config' was not specified."
        )

    if not sweep_dir or not os.path.isdir(sweep_dir):
        raise RuntimeError(
            f"[ERROR] run_ensemble function has been called, "
            f"but the parameter 'sweep_dir' was not specified: {sweep_dir}"
        )

    if sweep_on_remote is False:
        sweepdir_items_all = [
            f for f in os.listdir(sweep_dir)
            if os.path.isdir(os.path.join(sweep_dir, f))
        ]

        if not sweepdir_items_all:
            raise RuntimeError(
                f"[ERROR] No directories found in sweep_dir: {sweep_dir}")

        upsample_items = [item.strip()
                          for item in upsample.split(";")] if upsample else []

        if not upsample_items:
            upsample_items = sweepdir_items_all

        replica_counts_raw = str(
            args.get(
                "replicas",
                replica_start_number)).strip()

        if upsample_items:
            if ";" in replica_counts_raw:
                replica_counts = [int(x.strip())
                                  for x in replica_counts_raw.split(";")]
            else:
                replica_counts = [
                    int(replica_counts_raw)] * len(upsample_items)

            if len(replica_counts) != len(upsample_items):
                raise RuntimeError(
                    f"[ERROR] Mismatch between upsamples and replicas.\n"
                    f"Items ({len(upsample_items)}): {upsample_items}\n"
                    f"Counts ({len(replica_counts)}): {replica_counts}\n"
                    f"Each item in upsample must have exactly one replica."
                )

            if not set(upsample_items).issubset(set(sweepdir_items_all)):
                error = "[ERROR] upsample item: "
                error += f"{set(upsample_items) - set(sweepdir_items_all)}"
                error += " not found in SWEEP folder"
                raise RuntimeError(error)
            sweepdir_items = upsample_items
        else:
            sweepdir_items = sweepdir_items_all
            replica_counts = [1] * len(sweepdir_items)

        env.sweepdir_items = sweepdir_items
        env.replica_counts = replica_counts
    else:
        sweepdir_items = run("ls -1 {}".format(sweep_dir)).splitlines()
        if not sweepdir_items:
            raise RuntimeError(
                f"[ERROR] no valid directories found in {sweep_dir}")
        env.sweepdir_items = sweepdir_items
        env.replica_counts = [1] * len(sweepdir_items)

    # Always keep env.replica_counts as a list
    env.replica_counts = replica_counts

    # Set env.replicas to the common value if all are the same, else None
    if len(set(env.replica_counts)) == 1:
        env.replicas = env.replica_counts[0]
    else:
        env.replicas = None

    # reorder an exec_first item for priority execution.
    if hasattr(env, "exec_first") and env.exec_first in sweepdir_items:
        idx = sweepdir_items.index(env.exec_first)
        # Move both the sweepdir_item and its replica_count
        sweepdir_items.insert(0, sweepdir_items.pop(idx))
        replica_counts.insert(0, replica_counts.pop(idx))
        # Update env as well
        env.sweepdir_items = sweepdir_items
        env.replica_counts = replica_counts

    rich_print(f"[INFO] sweepdir_items: {env.sweepdir_items}")
    rich_print(f"[INFO] replica_counts: {env.replica_counts}")
    rich_print(f"[INFO] replicas: {env.replicas}")

    if execute_put_configs is True:
        execute(put_configs, config)

    # Submit via PilotJob
    if hasattr(env, "pj_type"):
        env.submit_job = False  # Only prepare, do not submit jobs directly
        job_args = dict(
            ensemble_mode=True,
            sweepdir_items=sweepdir_items,
            sweep_dir=sweep_dir,
            replica_start_number=1,
            replica_counts=replica_counts,
        )
        env.job_scripts_to_submit = job(job_args)
        pj_type = getattr(env, "pj_type", "").lower()
        rich_print(f"[INFO] Using PilotJob mode: {pj_type}")
        pj_dispatch = {
            "rp": run_radical,
            "qcg": run_qcg,
            "slurm-array": run_slurm_array,
            "slurm-manager": run_slurm_manager,
            "slurm": run_slurm_manager,
        }
        pilot_job_fn = pj_dispatch.get(pj_type)
        if pilot_job_fn:
            pilot_job_fn()
        else:
            supported_types = ', '.join(pj_dispatch.keys())
            raise RuntimeError(
                f"[ERROR] Unsupported pj_type '{pj_type}'. "
                f"Supported types are: {supported_types}"
            )
    else:
        env.submit_job = True  # Prepare and submit jobs
        job_args = dict(
            ensemble_mode=True,
            sweepdir_items=sweepdir_items,
            sweep_dir=sweep_dir,
            replica_start_number=1,
            replica_counts=replica_counts,
        )
        env.job_scripts_to_submit = job(job_args)

        rich_print("[INFO] Ensemble submission complete")


def run_radical():
    """
    Submit RADICAL-Pilot jobs using generated job scripts.
    """
    rich_print(
        Panel.fit(
            "NOW, we are submitting RADICAL-PilotJobs",
            title="[orange_red1]PJ job submission phase[/orange_red1]",
            border_style="orange_red1",
        )
    )
    update_environment()

    # Get SLURM resource parameters from configuration
    env.corespernode = getattr(env, "corespernode", 128)
    env.cpuspertask = getattr(env, "cpuspertask", 1)
    # Calculate nodes through standard FabSim3 method (cores/corespernode)
    calc_nodes()

    # Calculate total available resources
    env.total_cores = env.nodes * env.corespernode

    # Set RADICAL-Pilot specific parameters
    env.RP_PJ_NODES = env.nodes
    env.RP_PJ_CORES_PER_NODE = env.corespernode
    env.RP_PJ_TOTAL_CORES = env.total_cores
    env.RP_PJ_CORES_PER_TASK = getattr(env, "corespertask", env.cpuspertask)
    env.RP_PJ_GPUS_PER_TASK = getattr(env, "gpuspertask", 0)
    env.task_model = getattr(env, "task_model", "default")

    # RADICAL-Pilot specific configurations
    env.RP_PROJECT_ID = getattr(env, "project", None)
    env.RP_PARTITION_NAME = getattr(env, "partition", "standard")
    env.RP_QUEUE_NAME = getattr(env, "queue", "standard")
    env.RP_RUNTIME = getattr(env, "runtime", 30)

    # Display resource configuration
    rich_print(Panel.fit(
        f"[SLURM Resources]\n"
        f"Nodes: {env.nodes}\n"
        f"Cores per node: {env.corespernode}\n"
        f"CPUs per task: {env.cpuspertask}\n"
        f"Total cores: {env.total_cores}\n\n"
        f"[Radical-PJ Resources]\n"
        f"RP_PJ_NODES: {env.RP_PJ_NODES}\n"
        f"RP_PJ_CORES_PER_NODE: {env.RP_PJ_CORES_PER_NODE}\n"
        f"RP_PJ_TOTAL_CORES: {env.RP_PJ_TOTAL_CORES}",
        title="[bold blue]Radical-PilotJob Configuration[/bold blue]",
        border_style="blue"
    ))

    # Retrieve the job scripts to submit
    job_scripts_to_submit = getattr(env, "job_scripts_to_submit", [])
    if not job_scripts_to_submit:
        raise RuntimeError("[ERROR] No job scripts found to submit")

    print(f"[INFO] Found {job_scripts_to_submit} job scripts to submit")

    # Create run name from job name template (consistent with run_qcg)
    run_name = env.job_name_template_sh[:-3]

    # Generate task descriptions for each job using the template
    # This follows the exact same pattern as run_qcg()
    task_blocks = []
    for index, job_script in enumerate(job_scripts_to_submit, start=1):
        env.idsID = index
        env.idsPath = job_script

        # Set RADICAL-specific task parameters for the template
        env.task_descriptions = [env.idsPath]
        env.ranks = 1
        env.cores_per_rank = env.RP_PJ_CORES_PER_TASK
        # NOTE: No individual sandbox - all tasks use the pilot's shared

        # Generate the task description block using the template
        script_content = script_template_content("radical-PJ-task-template")
        task_blocks.append(script_content)

    rich_print(f"[INFO] Created {len(task_blocks)} RADICAL-Pilot tasks")

    # Indent and join all task blocks for the RADICAL manager script (like QCG)
    env.JOB_DESCRIPTIONS = textwrap.indent("\n".join(task_blocks), "    ")

    # Create a temporary working directory for RADICAL-Pilot runtime files
    rp_tmp_dir = Path(env.tmp_scripts_path) / "RP"
    rp_tmp_dir.mkdir(parents=True, exist_ok=True)

    # Create the unified sandbox directory for the entire RADICAL-Pilot session
    # This follows the RADICAL experts' recommendation
    env.rp_remote_dir = Path(env.results_path) / run_name / "RP"
    run("mkdir -p {}".format(env.rp_remote_dir))
    env.rp_remote_py = str(
        Path(env.rp_remote_dir) / f"rp_manager_{run_name}.py"
    )

    # Define the PILOT's unified sandbox directory
    env.RP_PILOT_SANDBOX = str(env.rp_remote_dir)

    # Create the RADICAL resource configuration directory structure
    # (following your original approach)
    sandbox_resources_path = rp_tmp_dir / ".radical" / "pilot" / "configs"
    sandbox_resources_path.mkdir(parents=True, exist_ok=True)

    # Handle resource configuration file in the proper RADICAL directory
    radical_resources_content = script_template_content("radical-resources")
    local_rp_config_path = sandbox_resources_path / "resource_fabsim.json"
    with open(local_rp_config_path, "w") as f:
        f.write(radical_resources_content)

    # Prepare and generate the RADICAL-Pilot main Python script
    rp_local_py = rp_tmp_dir / f"rp_manager_{run_name}.py"
    rp_pilot_script_content = script_template_content("radical-PJ-py")
    with open(rp_local_py, "w") as f:
        f.write(rp_pilot_script_content)
    os.chmod(rp_local_py, 0o755)

    # Create SLURM submission script
    rp_local_sh = rp_tmp_dir / f"rp_submit_{run_name}.sh"
    env.rp_remote_sh = Path(env.rp_remote_dir) / f"rp_submit_{run_name}.sh"

    # Define command to run RADICAL-Pilot script
    PJ_CMD = []
    PJ_CMD.append("# Run the Radical manager script")
    PJ_CMD.append(f"python3 {env.rp_remote_py}")
    env.run_radical_PilotJob = "\n".join(PJ_CMD)

    # Set job_results to the RP remote directory for this run
    env.job_results = env.rp_remote_dir

    # Render the RP submit bash script (SLURM header)
    rp_submit_content = script_template_content("radical-PJ-header")
    with open(rp_local_sh, "w") as f:
        f.write(rp_submit_content)
    os.chmod(rp_local_sh, 0o755)

    # Sync all RP files (pilot script, resource config, SLURM script)
    rsync_project(
        local_dir=str(rp_tmp_dir) + "/",
        remote_dir=str(env.rp_remote_dir) + "/",
    )

    # Submit the RP pilot job (via the SLURM script) to the scheduler
    job_submission(dict(job_script=str(env.rp_remote_sh)))
    rich_print("[INFO] RADICAL-Pilot job submitted successfully")


def run_qcg():
    """
    Submit QCG Pilot jobs using generated job scripts.
    """
    rich_print(
        Panel.fit(
            "NOW, we are submitting QCG-PilotJobs",
            title="[orange_red1]PJ job submission phase[/orange_red1]",
            border_style="orange_red1",
        )
    )
    update_environment()
    # Get SLURM resource parameters from configuration
    # Note: set cores in machines_user.yml to determine correct node count
    env.corespernode = getattr(env, "corespernode", 4)
    env.cpuspertask = getattr(env, "cpuspertask", 1)

    if hasattr(env, "machine_name") and env.machine_name != "localhost":
        # Remote HPC systems - maximize node utilization by default
        default_taskspernode = getattr(env, "corespernode", 128)
    else:
        # Localhost - conservative default
        default_taskspernode = 1

    env.taskspernode = getattr(env, "taskspernode", default_taskspernode)

    # Calculate nodes through standard FabSim3 method (cores/corespernode)
    calc_nodes()

    # Calculate total available resources
    env.total_cores = env.nodes * env.corespernode

    # Set QCG-specific parameters
    env.QCG_PJ_NODES = env.nodes
    env.QCG_PJ_CORES_PER_NODE = env.corespernode
    env.QCG_PJ_TOTAL_CORES = env.total_cores
    env.task_model = getattr(env, "task_model", "default")

    # Display resource configuration
    rich_print(Panel.fit(
        f"[SLURM Resources]\n"
        f"Nodes: {env.nodes}\n"
        f"Cores: {env.cores}\n"
        f"Cores per node: {env.corespernode}\n"
        f"CPUs per task: {env.cpuspertask}\n"
        f"Tasks per node: {env.taskspernode}\n"
        f"Total cores: {env.total_cores}\n\n"
        f"[QCG-PJ Resources]\n"
        f"QCG_PJ_NODES: {env.QCG_PJ_NODES}\n"
        f"QCG_PJ_CORES_PER_NODE: {env.QCG_PJ_CORES_PER_NODE}\n"
        f"QCG_PJ_TOTAL_CORES: {env.QCG_PJ_TOTAL_CORES}",
        title="[bold blue]QCG-PilotJob Configuration[/bold blue]",
        border_style="blue"
    ))

    # Retrieve the job scripts to submit
    job_scripts_to_submit = getattr(env, "job_scripts_to_submit", [])
    if not job_scripts_to_submit:
        raise RuntimeError("[ERROR] No job scripts found to submit")

    # Create run name from job name template
    run_name = env.job_name_template_sh[:-3]

    # Generate task descriptions for each job script
    task_blocks = []
    for index, job_script in enumerate(job_scripts_to_submit, start=1):
        env.idsID = index
        env.idsPath = job_script
        label, replica = env.job_script_info.get(job_script, ("", ""))

        # Set the correct path for job output
        if str(replica) == "1" and \
                env.replica_counts[env.sweepdir_items.index(label)] == 1:
            env.dirPath = os.path.join(
                env.results_path, run_name, "RUNS", label
            )
        else:
            env.dirPath = os.path.join(
                env.results_path, run_name, "RUNS", f"{label}_{replica}"
            )

        # Generate the task description from template
        script_content = script_template_content("qcg-PJ-task-template")
        task_blocks.append(script_content)

    rich_print(f"[INFO] Created {len(task_blocks)} task descriptions")

    # Indent and join all task blocks for the QCG manager script
    env.JOB_DESCRIPTIONS = textwrap.indent("\n".join(task_blocks), "    ")

    # Create a temporary working directory for QCG runtime files
    qcg_tmp_dir = Path(env.tmp_scripts_path) / "QCG"
    qcg_tmp_dir.mkdir(parents=True, exist_ok=True)

    # Prepare and generate the QCG manager Python script
    qcg_local_py = qcg_tmp_dir / f"qcg_manager_{run_name}.py"
    qcg_manager_content = script_template_content("qcg-PJ-py")
    with open(qcg_local_py, "w") as f:
        f.write(qcg_manager_content)
    os.chmod(qcg_local_py, 0o755)

    # Create the remote path for the QCG manager script
    env.qcg_remote_dir = Path(env.results_path) / run_name / "QCG"
    run("mkdir -p {}".format(env.qcg_remote_dir))
    env.qcg_remote_py = str(
        Path(env.qcg_remote_dir) / f"qcg_manager_{run_name}.py"
    )

    # Create SLURM submission script
    qcg_local_sh = qcg_tmp_dir / f"qcg_submit_{run_name}.sh"
    env.qcg_remote_sh = Path(env.qcg_remote_dir) / f"qcg_submit_{run_name}.sh"

    # Define command to run QCG-PilotJob manager
    PJ_CMD = []
    PJ_CMD.append("# Run the QCG manager script")
    PJ_CMD.append(f"python3 {env.qcg_remote_py}")
    env.run_QCG_PilotJob = "\n".join(PJ_CMD)

    # Set job_results to the QCG remote directory for this run
    env.job_results = env.qcg_remote_dir

    # Render the QCG submit bash script (SLURM header)
    qcg_submit_content = script_template_content("qcg-PJ-header")
    with open(qcg_local_sh, "w") as f:
        f.write(qcg_submit_content)
    os.chmod(qcg_local_sh, 0o755)

    # Sync all QCG files to the remote QCG directory
    rsync_project(
        local_dir=str(qcg_tmp_dir) + "/",
        remote_dir=str(env.qcg_remote_dir) + "/",
    )

    # Submit the QCG job to the scheduler
    job_submission(dict(job_script=env.qcg_remote_sh))
    rich_print("[INFO] QCG-PilotJob job submitted successfully")


def run_slurm_array():
    """
    Submit native SLURM job array using generated job scripts.
    """
    rich_print(
        Panel.fit(
            "NOW, we are submitting SLURM Job Arrays",
            title="[blue]SLURM Array job submission phase[/blue]",
            border_style="blue",
        )
    )

    # Standard FabSim3 environment and resource calculation
    update_environment()
    calc_nodes()

    # SLURM Array specific parameters
    env.SLURM_ARRAY_CORES_PER_TASK = getattr(env, "cpuspertask", 1)
    env.SLURM_ARRAY_MAX_CONCURRENT = getattr(env, "max_concurrent", 50)

    # Display resource configuration (following QCG pattern)
    rich_print(Panel.fit(
        f"[SLURM Resources]\n"
        f"Nodes: {env.nodes}\n"
        f"Cores per node: {env.corespernode}\n"
        f"Total cores: {env.nodes * env.corespernode}\n\n"
        f"[SLURM Array Resources]\n"
        f"Array size: {len(getattr(env, 'job_scripts_to_submit', []))}\n"
        f"Max concurrent: {env.SLURM_ARRAY_MAX_CONCURRENT}\n"
        f"Cores per task: {env.SLURM_ARRAY_CORES_PER_TASK}",
        title="[bold blue]SLURM Array Configuration[/bold blue]",
        border_style="blue"
    ))

    # Get job scripts from run_ensemble (same as QCG)
    job_scripts_to_submit = getattr(env, "job_scripts_to_submit", [])
    if not job_scripts_to_submit:
        raise RuntimeError("[ERROR] No job scripts found to submit")

    # Create run name (following QCG pattern)
    run_name = env.job_name_template_sh[:-3]

    # Create task file (key difference from QCG - simpler!)
    env.SLURM_ARRAY_SIZE = len(job_scripts_to_submit)

    # Create temporary working directory (following QCG pattern)
    array_tmp_dir = Path(env.tmp_scripts_path) / "SLURM_ARRAY"
    array_tmp_dir.mkdir(parents=True, exist_ok=True)

    # Create task list file (core of SLURM array approach)
    task_list_content = []
    for index, job_script in enumerate(job_scripts_to_submit, start=1):
        # Extract job information
        label, replica = env.job_script_info.get(job_script, ("", ""))

        # Set correct output path (following QCG pattern)
        if str(replica) == "1" and \
                env.replica_counts[env.sweepdir_items.index(label)] == 1:
            output_dir = os.path.join(
                env.results_path, run_name, "RUNS", label
            )
        else:
            output_dir = os.path.join(
                env.results_path, run_name, "RUNS", f"{label}_{replica}"
            )

        # Create task command (much simpler than QCG!)
        task_cmd = f"cd {output_dir} && bash {job_script}"
        task_list_content.append(task_cmd)

    # Write task list file
    task_list_file = array_tmp_dir / f"task_list_{run_name}.txt"
    with open(task_list_file, "w") as f:
        for task in task_list_content:
            f.write(f"{task}\n")

    # Set environment variables for template
    env.array_remote_dir = Path(env.results_path) / run_name / "SLURM_ARRAY"
    run("mkdir -p {}".format(env.array_remote_dir))
    array_task_list_filename = f"task_list_{run_name}.txt"
    array_task_list_path = Path(env.array_remote_dir)
    array_task_list_path = array_task_list_path / array_task_list_filename
    env.array_task_list = str(array_task_list_path)

    # Create SLURM submission script (following QCG template pattern)
    array_local_sh = array_tmp_dir / f"slurm_array_submit_{run_name}.sh"
    array_sh_name = f"slurm_array_submit_{run_name}.sh"
    env.array_remote_sh = Path(env.array_remote_dir) / array_sh_name

    # Set job_results for template processing
    env.job_results = env.array_remote_dir

    # Generate SLURM array script using template
    array_submit_content = script_template_content("slurm-array-PJ-header")
    with open(array_local_sh, "w") as f:
        f.write(array_submit_content)
    os.chmod(array_local_sh, 0o755)

    # Sync files to remote (following QCG pattern)
    rsync_project(
        local_dir=str(array_tmp_dir) + "/",
        remote_dir=str(env.array_remote_dir) + "/",
    )

    # Submit the SLURM array job (following QCG pattern)
    job_submission(dict(job_script=str(env.array_remote_sh)))
    rich_print("[INFO] SLURM Array job submitted successfully")


def run_slurm_manager():
    """
    Submit single SLURM job that internally manages multiple tasks.
    Similar to QCG but without Python dependencies.
    """
    rich_print(
        Panel.fit(
            "NOW, we are submitting SLURM Manager Job",
            title="[blue]SLURM Manager job submission phase[/blue]",
            border_style="blue",
        )
    )

    # Standard FabSim3 environment and resource calculation
    update_environment()
    calc_nodes()

    # Get job scripts from run_ensemble
    job_scripts_to_submit = getattr(env, "job_scripts_to_submit", [])
    if not job_scripts_to_submit:
        raise RuntimeError("[ERROR] No job scripts found to submit")

    # Create run name
    run_name = env.job_name_template_sh[:-3]

    # SLURM Manager specific parameters
    env.SLURM_MANAGER_CORES_PER_TASK = getattr(env, "cpuspertask", 1)
    env.SLURM_MANAGER_MAX_CONCURRENT = getattr(env, "max_concurrent", 4)
    env.SLURM_MANAGER_TOTAL_TASKS = len(job_scripts_to_submit)

    # Display resource configuration
    rich_print(Panel.fit(
        f"[SLURM Resources]\n"
        f"Nodes: {env.nodes}\n"
        f"Cores per node: {env.corespernode}\n"
        f"Total cores: {env.nodes * env.corespernode}\n\n"
        f"[SLURM Manager Resources]\n"
        f"Total tasks: {env.SLURM_MANAGER_TOTAL_TASKS}\n"
        f"Max concurrent: {env.SLURM_MANAGER_MAX_CONCURRENT}\n"
        f"Cores per task: {env.SLURM_MANAGER_CORES_PER_TASK}",
        title="[bold blue]SLURM Manager Configuration[/bold blue]",
        border_style="blue"
    ))

    # Create temporary working directory
    manager_tmp_dir = Path(env.tmp_scripts_path) / "SLURM_MANAGER"
    manager_tmp_dir.mkdir(parents=True, exist_ok=True)

    # Create task list file with full commands
    task_list_content = []
    for index, job_script in enumerate(job_scripts_to_submit, start=1):
        label, replica = env.job_script_info.get(job_script, ("", ""))

        # Set correct output path
        if str(replica) == "1" and \
                env.replica_counts[env.sweepdir_items.index(label)] == 1:
            output_dir = os.path.join(
                env.results_path, run_name, "RUNS", label
            )
        else:
            output_dir = os.path.join(
                env.results_path, run_name, "RUNS", f"{label}_{replica}"
            )

        # Create task command
        task_cmd = f"cd {output_dir} && bash {job_script}"
        task_list_content.append(task_cmd)

    # Write task list file
    task_list_file = manager_tmp_dir / f"task_list_{run_name}.txt"
    with open(task_list_file, "w") as f:
        for i, task in enumerate(task_list_content, 1):
            f.write(f"{i}: {task}\n")

    # Set environment variables for template
    manager_remote_dir = Path(env.results_path) / run_name / "SLURM_MANAGER"
    env.manager_remote_dir = manager_remote_dir
    run("mkdir -p {}".format(env.manager_remote_dir))
    task_list_filename = f"task_list_{run_name}.txt"
    env.manager_task_list = Path(env.manager_remote_dir) / task_list_filename
    env.manager_task_list = str(env.manager_task_list)

    # Create SLURM submission script
    manager_local_sh = manager_tmp_dir / f"slurm_manager_submit_{run_name}.sh"
    manager_sh_name = f"slurm_manager_submit_{run_name}.sh"
    env.manager_remote_sh = Path(env.manager_remote_dir) / manager_sh_name

    # Set job_results for template processing
    env.job_results = env.manager_remote_dir

    # Generate SLURM manager script using template
    manager_submit_content = script_template_content("slurm-manager-PJ-header")
    with open(manager_local_sh, "w") as f:
        f.write(manager_submit_content)
    os.chmod(manager_local_sh, 0o755)

    # Sync files to remote
    rsync_project(
        local_dir=str(manager_tmp_dir) + "/",
        remote_dir=str(env.manager_remote_dir) + "/",
    )

    # Submit the SLURM manager job
    job_submission(dict(job_script=str(env.manager_remote_sh)))
    rich_print("[INFO] SLURM Manager job submitted successfully")


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
            # Pure Python implementation for float ranges
            start, stop, step = vals
            result = []
            current = start
            while current < stop:
                result.append(ttype(current))
                current += step
            return result
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
    env.dest_name = env.pather.join(
        env.scripts_path, env.pather.basename(env.job_script)
    )

    # Send Install script to remote machine
    put(env.job_script, env.dest_name)
    #
    run(template("mkdir -p $job_results"))
    run(template("{} {}".format(env.job_dispatch, env.dest_name)),
        cd=env.pather.dirname(env.job_results))

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
                "$username@$remote:$app_repository".format(
                    tmp_app_dir, whl
                )
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


@task
def create_virtual_env(path_suffix="VirtualEnv", system_packages=True):
    """
    Create or verify Python virtual environment with HPC awareness.
    """
    update_environment()

    # Check if already configured and verify it exists
    if hasattr(env, "virtual_env_path") and env.virtual_env_path:
        verify_cmd = f"test -f {env.virtual_env_path}/bin/activate"
        try:
            result = run(
                f"{verify_cmd} && echo 'EXISTS' || echo 'MISSING'",
                capture=True,
                warn_only=True
            )

            if "EXISTS" in result:
                # Test that it can be activated
                activate_cmd = f"source {env.virtual_env_path}/bin/activate"
                test_cmd = "python --version"
                test_result = run(
                    f"{activate_cmd} && {test_cmd}",
                    capture=True,
                    warn_only=True
                )
                if test_result.succeeded:
                    rich_print(
                        Panel.fit(
                            f"Virtual environment: {env.virtual_env_path}\n"
                            f"Python: {test_result.strip()}",
                            title="[green]Virtual Environment Ready[/green]",
                            border_style="green",
                        ))
                    return env.virtual_env_path
        except Exception:
            pass

    # Generic HPC configuration (cray-python works on most systems)
    if env.machine_name == "localhost":
        base_path = env.localroot
        modules = []
    else:
        # Generic HPC path structure and modules
        base_path = f"/work/{env.project}/{env.project}/{env.username}"
        modules = ["cray-python"]  # Default for most HPC systems

    venv_path = f"{base_path}/{path_suffix}"

    # Create the virtual environment
    cmd_parts = []
    if modules:
        cmd_parts.extend([f"module load {mod}" for mod in modules])

    system_pkg_flag = "--system-site-packages" if system_packages else ""
    cmd_parts.extend([
        f"mkdir -p {base_path}",
        f"python3 -m venv {system_pkg_flag} {venv_path}",
        f"test -f {venv_path}/bin/activate && echo 'SUCCESS' || echo 'FAILED'"
    ])

    try:
        result = run(" && ".join(cmd_parts), capture=True)
        if "SUCCESS" in result:
            rich_print(
                Panel.fit(
                    f"Virtual environment created: {venv_path}\n\n"
                    f"Add to machines_user.yml under '{env.machine_name}': \n"
                    f"  virtual_env_path: \"{venv_path}\"\n\n"
                    f"Then install applications: \n"
                    f"  fabsim {env.machine_name} install_app: QCG-PilotJob",
                    title="[green]Virtual Environment Created[/green]",
                    border_style="green",
                ))
            return venv_path
        else:
            raise RuntimeError("Virtual environment creation failed")

    except Exception as e:
        rich_print(
            Panel.fit(
                f"Failed to create virtual environment: {str(e)}\n\n"
                f"This usually means: \n"
                f"1. Python3 not available - try different modules\n"
                f"2. No write permissions to {base_path}\n"
                f"3. Insufficient disk space",
                title="[red]Creation Failed[/red]",
                border_style="red",
            ))
        return None


@task
def direct_install_app(name="", venv="True"):
    """
    Install a Python application in a virtual env on a remote machine.

    Args:
        name (str): Name of the package to install (e.g., "QCG-PilotJob")
        venv (str): Whether to use a virtual env ("True" or "False")
    """
    update_environment()

    if not name:
        rich_print(
            Panel.fit(
                "No application name provided. Please specify to install.",
                title="[yellow]Installation Error[/yellow]",
                border_style="yellow",
            ))
        return

    # 1. Create virtual environment if needed
    if venv.lower() == "true":
        if not hasattr(env, "virtual_env_path") or not env.virtual_env_path:
            rich_print("[INFO] Creating a new virtual environment...")
            env.virtual_env_path = create_virtual_env()
        rich_print(f"[INFO] Using virtual env: {env.virtual_env_path}")

    # 2 & 3. Activate virtual env and install the application directly
    rich_print(f"[INFO] Installing {name}...")

    # Prepare installation command
    cmd = []

    # Add machine-specific module loading if needed
    if env.machine_name == "archer2":
        cmd.append("module load cray-python")

    # Activate virtual environment if requested
    if venv.lower() == "true":
        cmd.append(f"source {env.virtual_env_path}/bin/activate")

    # Install with pip
    install_options = "--user" if venv.lower() != "true" else ""
    cmd.append(f"pip install {install_options} {name}")

    # Run the installation command
    try:
        result = run(" && ".join(cmd))
        rich_print(
            Panel.fit(
                f"{name} installation completed successfully in "
                f"{'venv' if venv.lower() == 'true' else 'user space'}",
                title="[green]Installation Success[/green]",
                border_style="green",
            )
        )
    except Exception as e:
        rich_print(
            Panel.fit(
                f"Error installing {name}: {str(e)}\n\n"
                f"You may need to install development libraries, or"
                f"resolve dependencies manually.",
                title="[red]Installation Failed[/red]",
                border_style="red",
            )
        )
