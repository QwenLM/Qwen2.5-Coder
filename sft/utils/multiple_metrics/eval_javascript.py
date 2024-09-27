import os
import subprocess
from pathlib import Path


def eval_script(path: Path):
    try:
        # Assumes exit-code 0 is all okay
        output = subprocess.run(["node", str(path)], capture_output=True, timeout=5)

        if output.returncode == 0:
            status = "OK"
        else:
            outmessage = str(output)
            if "ERR_ASSERTION" in outmessage:
                status = "AssertionError"
            elif "SyntaxError" in outmessage:
                status = "SyntaxError"
            elif "ReferenceError" in outmessage:
                status = "ReferenceError"
            else:
                status = "Exception"
        returncode = output.returncode
    except subprocess.TimeoutExpired as exc:
        status = "Timeout"
        output = exc
        returncode = -1
    except subprocess.CalledProcessError as exc:
        status = "Exception"
        returncode = exc.returncode
        output = exc
    return {
        "status": status,
        "exit_code": returncode,
        "stdout": "" if output.stdout is None else output.stdout.decode("utf-8"),
        "stderr": "" if output.stderr is None else output.stderr.decode("utf-8"),
    }


def main():
    directory = Path(
        Path(__file__).parent, "..", "datasets", "js-keep-code_davinci_001_temp_0.2"
    ).resolve()

    for filename in os.listdir(directory):
        r = eval_script(Path.joinpath(directory, filename))
        filename = filename.split(".")[0]
        print(f"JavaScript,{filename},{r['status']}")


if __name__ == "__main__":
    main()
