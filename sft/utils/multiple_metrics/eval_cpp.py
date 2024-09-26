from pathlib import Path

from .generic_eval import main
from .safe_subprocess import run

LANG_NAME = "C++"
LANG_EXT = ".cpp"


def eval_script(path: Path):
    basename = ".".join(str(path).split(".")[:-1])
    build_result = run(["g++", path, "-o", basename, "-std=c++17"])
    if build_result.exit_code != 0:
        return {
            "status": "SyntaxError",
            "exit_code": build_result.exit_code,
            "stdout": build_result.stdout,
            "stderr": build_result.stderr,
        }

    run_result = run([basename])
    if "In file included from /shared/centos7/gcc/9.2.0-skylake/" in run_result.stderr:
        raise Exception("Skylake bug encountered")
    if "/4.8.2" in run_result.stderr:
        raise Exception("Ancient compiler encountered")
    if run_result.timeout:
        status = "Timeout"
    elif run_result.exit_code != 0:
        status = "Exception"
    else:
        status = "OK"
    return {
        "status": status,
        "exit_code": run_result.exit_code,
        "stdout": run_result.stdout,
        "stderr": run_result.stderr,
    }


if __name__ == "__main__":
    main(eval_script, LANG_NAME, LANG_EXT)
