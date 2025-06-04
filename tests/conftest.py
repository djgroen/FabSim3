import pytest
import subprocess


@pytest.fixture
def execute_cmd(request):
    try:
        proc = subprocess.Popen(
            request.param,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        stdout, _ = proc.communicate()
        output = stdout.decode("utf-8")
    except Exception as e:
        raise RuntimeError(f"Unexpected error while executing '{request.param}': {e}")

    if proc.returncode != 0:
        # Print stdout even if it fails, for CI visibility
        print(f"Command output:\n{output}")
        raise RuntimeError(
            f"\njob execution encountered an error (return code {proc.returncode})"
            f"\nwhile executing: '{request.param}'"
            f"\n\nOutput:\n{output}"
        )

    yield output
    proc.terminate()
