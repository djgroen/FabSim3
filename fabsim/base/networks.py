from __future__ import print_function

import os
import subprocess
from contextlib import contextmanager

from beartype import beartype
from beartype.typing import List, Optional, Tuple
from fabric2 import Config, Connection

from fabsim.base.env import env
from fabsim.base.utils import add_print_prefix
from fabsim.deploy.templates import template


@beartype
def local(command: str, capture: Optional[bool] = False) -> Tuple[str, str]:
    """
    Run a command on the local system.

    Args:
        command (str): the command to be executed
        capture (bool, optional): if `False`, the local subprocess will use
            your terminal for stdout and stderr. Otherwise, if `True`, then
            nothing will be printed in the terminal, and any subprocess'
            stdout/stderr will be captured and returned.

        shell (None, optional): Description
    """

    with add_print_prefix(prefix="local", color=196):
        print("{}".format(command))

    # set stdout and stderr for subprocess
    if capture:
        stdout = subprocess.PIPE
        stderr = subprocess.PIPE
    else:
        # TODO: need to be refined in case of global logging option
        stdout = None
        stderr = None

    # execute the command on the local system
    try:
        p = subprocess.Popen(command, shell=True, stdout=stdout, stderr=stderr)
        # p.wait()
        # yield f"{command} Rsync process completed."
        (stdout, stderr) = p.communicate()

    except Exception as e:
        raise RuntimeError("Unexpected error: {}".format(e))
        # sys.exit()

    if p.returncode not in env.acceptable_err_subprocesse_ret_codes:
        raise RuntimeError(
            "\nlocal() encountered an error (return code {})"
            "while executing '{}'".format(p.returncode, command)
        )
        # sys.exit(0)

    stdout = stdout.decode("utf-8").strip() if stdout else ""
    stderr = stderr.decode("utf-8").strip() if stderr else ""

    return (stdout, stderr)


class HostConnection:
    def __init__(self):
        self.host_address = env.remote
        self.user = env.username
        self.port = env.port
        self.use_sudo = env.use_sudo
        self.pty = True

    @contextmanager
    def ssh_connection(self):
        """
        Make and establish a fabric ssh connection
        """

        conn = Connection(
            host=self.host_address,
            user=self.user,
            port=self.port,
            config=None,
            gateway=None,
            forward_agent=False,
            connect_timeout=None,
            connect_kwargs=None,
            inline_ssh_env=False,
        )

        try:
            print("host_address:", self.host_address)
            print("user:", self.user)
            print("port:", self.port)
            # print('password:', self.password)
            print("\x1b[6;30;42m" + "Opening a connection!" + "\x1b[0m")
            conn.open()
            yield conn
        finally:
            print("\x1b[6;30;45m" + "Closing a connection!" + "\x1b[0m")
            conn.close()

    def run_command(self, command, cd=None, capture=False):
        """
        exec a command on the target remote machine
        """
        # TODO: implement the hide options here

        # this will load the login shell. this required to make sure
        # the module command can be found during job execution
        command = 'bash -l -c "{}"'.format(command)

        # env.remote : localhost
        # env.host_string : user@localhost
        with add_print_prefix(
            prefix="run on {}".format(env.host_string), color=196
        ):
            print("{}".format(command))

        # (None, False, 'out', 'stdout', 'err', 'stderr', 'both', True)
        hide = None
        if capture is True:
            # here, I only set to hide the stdout, and capture any stderr
            hide = "out"
        with add_print_prefix(prefix=env.host_string):
            with self.ssh_connection() as conn:
                run = conn.sudo if self.use_sudo else conn.run
                if cd is None:
                    result = run(command, pty=self.pty, hide=hide)

                else:
                    with conn.cd(cd):
                        result = run(command, pty=self.pty, hide=hide)
        return result.stdout


@beartype
def run(cmd: str, cd: Optional[str] = None, capture: Optional[bool] = False):
    if env.manual_sshpass:
        return manual_sshpass(cmd, cd=cd, capture=capture)
    elif env.manual_gsissh:
        return manual_gsissh(cmd, cd=cd, capture=capture)
    elif env.manual_ssh:
        return manual(cmd, cd=cd, capture=capture)
    else:
        return _run(cmd, cd=cd, capture=capture)


@beartype
def manual_sshpass(
    cmd: str, cd: Optional[str] = None, capture: Optional[bool] = False
):
    if env.get("command_prefixes"):
        commands = env.command_prefixes[:]
    else:
        commands = []

    if env.get("cwd"):
        commands.append("cd {}".format(env.cwd))

    commands.append(cmd)
    manual_command = " && ".join(commands)
    if not hasattr(env, "sshpass") and not env.env_sshpass:
        raise ValueError("Neither SSHPASS set in environment" +
                         " nor sshpass value set for this remote machine")
    sshpass_args = "-e" if env.env_sshpass else "-f '%(sshpass)s'" % env
    pre_cmd = f"sshpass {sshpass_args}" + " ssh %(username)s@%(remote)s " % env
    return local(pre_cmd + "'" + manual_command + "'", capture=capture)


@beartype
def manual_gsissh(
    cmd: str, cd: Optional[str] = None, capture: Optional[bool] = False
):
    # From the fabric wiki, bypass fabric internal ssh control
    if env.get("command_prefixes"):
        commands = env.command_prefixes[:]
    else:
        commands = []

    if env.get("cwd"):
        commands.append("cd {}".format(env.cwd))

    commands.append(cmd)
    manual_command = " && ".join(commands)
    pre_cmd = "gsissh -t -p %(port)s %(remote)s " % env
    return local(pre_cmd + "'" + manual_command + "'", capture=capture)


@beartype
def manual(
    cmd: str, cd: Optional[str] = None, capture: Optional[bool] = False
):
    # From the fabric wiki, bypass fabric internal ssh control
    if env.get("command_prefixes"):
        commands = env.command_prefixes[:]
    else:
        commands = []

    if env.get("cwd"):
        commands.append("cd {}".format(env.cwd))

    commands.append(cmd)
    manual_command = " && ".join(commands)
    pre_cmd = "ssh -Y -p %(port)s %(username)s@%(remote)s " % env

    return local(pre_cmd + "'" + manual_command + "'", capture=capture)
    # return local(pre_cmd + "'" + manual_command + "'", capture=capture)
    # return local(pre_cmd, capture=capture)


def _run(cmd: str, cd: str = None, capture: bool = False):
    """
    Execute a command on the remote machine.

    """
    conn = HostConnection()

    return conn.run_command(command=cmd, cd=cd, capture=capture)


@beartype
def rsync_project(
    remote_dir: str,
    local_dir: str,
    exclude: List[str] = [],
    delete: Optional[bool] = False,
    ssh_opts: Optional[str] = "",
    default_opts: Optional[str] = "-pthrvz",
    capture: Optional[bool] = False,
    quiet: Optional[bool] = False,
) -> Tuple[str, str]:
    """
    Synchronize a remote directory with the current project directory via
    `rsync`. It uses the env variables (such as user, remote machine address,
    and port) to prepare the needed input options for `rsync` command.

    Args:
        remote_dir (str): the path to the directory on the remote machine.
        local_dir (str): the path to the local directory as the source
            directory
        exclude (list, optional): the list of files/folders to be excluded.
            The list will be pass to `--exclude` option via `rsync` command.
            For example, the input `exclude=['file1.txt','dir1/*','dir2']` will
            be send to `rsync` command as :
            `--exclude={'file1.txt','dir1/*','dir2'}`
        delete (bool, optional): a boolean flag which indicates whether
            the `--delete` option should be passed via `rsync` command or not.
        ssh_opts (str, optional): the extra input args for the SSH options
            string, such as `--rsh` flag.
        default_opts (str, optional): the default rsync options `-pthrvz`,
            override if desired to remove verbosity

    !!! note
        Please make sure both input arguments `remote_dir` and `local_dir`
        ended with a trailing slash.
    """

    # check if input args remote_dir and local_dir end by a trailing slash
    # or not
    if not remote_dir.endswith("/"):
        remote_dir = remote_dir + "/"
    if not local_dir.endswith("/"):
        local_dir = local_dir + "/"

    # create --exclude options from exclude list
    if len(exclude) > 0:
        exclude_opts = "--exclude={%s}" % (
            ",".join(["'{}'".format(item) for item in exclude])
        )
    else:
        exclude_opts = ""

    # add --delete options if needed
    delete_opt = "--delete" if delete is True else ""

    # add --quiet option if needed
    quiet_opt = "--quiet" if quiet is True else ""

    # set port arg
    port_opt = "-p {}".format(env.port)

    # set RSH arg
    rsh_opts = "--rsh='ssh {}'".format(" ".join([port_opt, ssh_opts]))

    rync_cmd = "rsync {} {} {} {} {} {} {}:{}".format(
        delete_opt,
        exclude_opts,
        quiet_opt,
        default_opts,
        rsh_opts,
        local_dir,
        env.host_string,
        remote_dir,
    )
    # rync_cmd = "rsync --delete -pthrvz {} {} {}:{}".format(
    #      exclude_opts,
    #     local_dir, env.host_string, remote_dir
    # )

    with add_print_prefix(prefix="rsync_project", color=196):
        print("{}".format(rync_cmd))
    # conn = HostConnection()
    # return conn.run_command(command=rync_cmd, capture=capture)

    return local(command=rync_cmd, capture=capture)
    # return rync_cmd, capture
    # return _run(cmd=rync_cmd, capture=capture)


@beartype
def put(
    src: str, dst: str, capture: Optional[bool] = False
) -> Tuple[str, str]:
    """
    Upload a file or directory to a remote host.

    !!! note
        In case of `isdir(src) = True`
        - if `dst` ends with `/`, then `src` contents and not the directory
            itself (i.e., all files and sub-directories) will be copied to the
            root of `dst` folder
        - if `dst` *NOT* ends with `/`, the directory  `src` itself with all
            contents will copied to `dst` folder

    Args:
        src (str): is a absolute local file or directory path in local PC
        dst (str): is a absolute location path on remote host

    """
    if not (os.path.isfile(src) or os.path.isdir(src)):
        # src should points to a regular file or a directory
        raise RuntimeError(
            "\nThe input path {} is no file neither folder !!! ".format(src)
        )
        # sys.exit()

    # if src points to a directory, then remove '/' from end of src if exists
    if os.path.isdir(src):
        src = src.rstrip("/")

    if os.path.isfile(src) and os.path.isdir(dst) and not dst.endswith("/"):
        dst = dst + "/"

    if os.path.isdir(src) and os.path.isdir(dst) and dst.endswith("/"):
        src = src + "/*"

    pu_cmd = ""
    if env.manual_gsissh:
        # TODO : I did not test globus-url-copy, and used the initialize code
        if os.path.isdir(src):
            # if src[-1] != "/":
            if not src.endswith("/"):
                env.manual_src = src + "/"
                env.manual_dest = dst + "/"
        else:
            env.manual_src = src
            env.manual_dest = dst
        put_cmd = template(
            "globus-url-copy -sync -r -cd -p 10 "
            "file://$manual_src gsiftp://$host/$manual_dest"
        )
    elif env.manual_ssh:
        scp_opt = ""
        if os.path.isdir(src.rstrip("*")):
            scp_opt = "-rp"

        put_cmd = "scp {} {} {}:{}".format(scp_opt, src, env.host_string, dst)
    else:
        # here, instead of sftp program used by Fabric, I decided to use rsync
        # which is much faster in case of having folder as input src arg

        default_opts = "-pthrvz"
        # set port arg
        port_opt = "-p {}".format(env.port)

        # set RSH arg
        rsh_opts = "--rsh='ssh {}'".format(port_opt)

        put_cmd = "rsync {} {} {} {}:{}".format(
            default_opts, rsh_opts, src, env.host_string, dst
        )

    with add_print_prefix(prefix="put", color=196):
        print("{}".format(put_cmd))

    return local(command=put_cmd, capture=capture)
