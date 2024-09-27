from pathlib import Path
import subprocess
from .safe_subprocess import run


def eval_script(path: Path):
    """
    npm install -g typescript
    """
    #try:
    r = run(["tsc", "--target", "esnext", str(path)], timeout_seconds=15)
    # except:
    #     subprocess.run("npm install -g typescript")
    if r.exit_code != 0:
        return {
            "status": "SyntaxError",
            "exit_code": r.exit_code,
            "stdout": r.stdout,
            "stderr": r.stderr,
        }

    r = run(["node", str(path).replace(".ts", ".js")], timeout_seconds=15)
    if r.timeout:
        status = "Timeout"
    elif r.exit_code == 0:
        status = "OK"
    elif "ERR_ASSERTION" in r.stderr:
        status = "AssertionError"
    elif "SyntaxError" in r.stderr:
        status = "SyntaxError"
    elif "ReferenceError" in r.stderr:
        status = "ReferenceError"
    else:
        status = "Exception"
    return {
        "status": status,
        "exit_code": r.exit_code,
        "stdout": r.stdout,
        "stderr": r.stderr,
    }
