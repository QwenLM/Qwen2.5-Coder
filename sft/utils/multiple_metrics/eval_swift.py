import os
import subprocess
from pathlib import Path

from .safe_subprocess import run


def eval_script(path: Path):
    basename = ".".join(str(path).split(".")[:-1])
    r = run(["swiftc", path, "-o", basename], timeout_seconds=45)
    if r.timeout:
        status = "Timeout"
    elif r.exit_code != 0:
        # Well, it's a compile error. May be a type error or
        # something. But, why break the set convention
        status = "SyntaxError"
    else:
        r = run([basename], timeout_seconds=5)
        if r.timeout:
            status = "Timeout"
        elif r.exit_code != 0:
            # Well, it's a panic
            status = "Exception"
        else:
            status = "OK"
        os.remove(basename)
    return {
        "status": status,
        "exit_code": r.exit_code,
        "stdout": r.stdout,
        "stderr": r.stderr,
    }
