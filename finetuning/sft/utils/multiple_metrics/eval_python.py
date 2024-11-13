from pathlib import Path
import os
from .safe_subprocess import run


def eval_script(path: Path):
    os.environ["PATH"] = "miniconda3/envs/qwen/bin/:" + os.environ["PATH"]
    r = run(["python", str(path)])
    if r.timeout:
        status = "Timeout"
    elif r.exit_code == 0:
        status = "OK"
    elif "SyntaxError" in r.stderr:
        status = "SyntaxError"
    else:
        status = "Exception"
    return {
        "status": status,
        "exit_code": r.exit_code,
        "stdout": r.stdout,
        "stderr": r.stderr,
    }
