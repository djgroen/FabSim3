import os
import pytest
import subprocess

@pytest.fixture
def execute_cmd(request):
    cmd = request.param

    # If using 'fabsim' at beginning, replace with full path
    if cmd.strip().startswith("fabsim "):
        fabsim_path = os.path.join(os.getcwd(), "fabsim", "bin", "fabsim")
        cmd = cmd.replace("fabsim", fabsim_path, 1)

    try:
        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        stdout, _ = proc.communicate()
        output = stdout.decode("utf-8")
    except Exception as e:
        raise RuntimeError(f"Unexpected error while executing '{cmd}': {e}")

    if proc.returncode != 0:
        print(f"Command output:\n{output}")
        raise RuntimeError(
            f"\njob execution encountered an error (return code {proc.returncode})"
            f"\nwhile executing: '{cmd}'"
            f"\n\nOutput:\n{output}"
        )

    yield output
    proc.terminate()
