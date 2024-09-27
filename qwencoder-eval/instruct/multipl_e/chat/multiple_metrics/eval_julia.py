from pathlib import Path

from .safe_subprocess import run


def eval_script(path: Path):
    result = run(["julia", str(path)], timeout_seconds=5)
    if result.timeout:
        status = "Timeout"
    elif result.exit_code == 0:
        status = "OK"
    # TODO(arjun): I would like this to be reviewed more carefully by John.
    elif len(result.stderr) < 1:
        status = "Exception"
    else:
        status = "SyntaxError"

    return {
        "status": status,
        "exit_code": result.exit_code,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
