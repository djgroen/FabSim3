import pytest
import subprocess


@pytest.fixture
def execute_cmd(request):
    cmds = request.param.split()
    try:
        proc = subprocess.Popen(
            request.param,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        (stdout, stderr) = proc.communicate()
    except Exception as e:
        raise RuntimeError("Unexpected error: {}".format(e))

    acceptable_err_subprocesse_ret_codes = [0]
    if proc.returncode not in acceptable_err_subprocesse_ret_codes:
        raise RuntimeError(
            "\njob execution encountered an error (return code {})"
            "while executing '{}'".format(proc.returncode, request.param)
        )
    yield stdout.decode("utf-8")
    proc.terminate()
