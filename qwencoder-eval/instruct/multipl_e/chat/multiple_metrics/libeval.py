import os
import signal
import subprocess
from typing import List

from . import generic_eval


def testing_mail(x, y, z):
    generic_eval.gmain(x, y, z)


def run_without_exn(args: List[str]):
    """
    Runs the given program with a five second timeout. Does not throw an exception
    no matter what happens. The output is a dictionary of the format that we expect
    for our evaluation scripts. The "status" field is "OK" when the exit code is
    zero. If that isn't enough, you may want to tweak the status based on the
    captured stderr and stdout.
    """
    p = subprocess.Popen(
        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True
    )
    try:
        stdout, stderr = p.communicate(timeout=5)
        exit_code = p.returncode
        status = "OK" if exit_code == 0 else "Exception"
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = p.stdout.read(), p.stderr.read()
        os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        exit_code = -1
        status = "Timeout"

    if stdout is None:
        stdout = b""
    if stderr is None:
        stderr = b""
    return {
        "status": status,
        "exit_code": exit_code,
        "stdout": stdout.decode("utf-8", errors="ignore"),
        "stderr": stderr.decode("utf-8", errors="ignore"),
    }
