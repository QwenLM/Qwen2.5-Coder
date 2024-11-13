import argparse
import subprocess
from pathlib import Path

from .generic_eval import main as gmain


def eval_script(path: Path):
    try:
        # Assumes exit-code 0 is all okay
        # Need check=True for Ruby to pass errors to CalledProcessError
        output = subprocess.run(
            ["ruby", path], check=True, capture_output=True, timeout=5
        )
        if output.returncode == 0:
            status = "OK"
            out = output.stderr
            error = output.stdout
            returncode = 0
        else:
            raise Exception("there's an issue with check = True for Ruby, INVESTIGATE!")
    except subprocess.TimeoutExpired as exc:
        status = "Timeout"
        out = exc.stdout
        error = exc.stderr
        returncode = -1
    except subprocess.CalledProcessError as exc:
        returncode = exc.returncode
        out = exc.stdout
        error = exc.stderr
        # failure with code 1 but no error message is an Exception from Failed tests
        if len(error) < 1:
            status = "Exception"
        else:  # everything that prints out an error message is a SyntaxError
            status = "SyntaxError"
    return {
        "status": status,
        "exit_code": returncode,
        "stdout": out,
        "stderr": error,
    }


if __name__ == "__main__":
    gmain(eval_script, "Ruby", ".rb")
