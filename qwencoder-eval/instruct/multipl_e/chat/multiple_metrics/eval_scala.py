import tempfile
from pathlib import Path

from .safe_subprocess import run

LANG_NAME = "Scala"
LANG_EXT = ".scala"


def eval_script(path: Path):
    with tempfile.TemporaryDirectory() as outdir:
        # Each Scala file contains the class with same name `JAVA_CLASS_NAME`
        # Hence, scalac will same JAVA_CLASS_NAME.class file for each problem
        # Write class for each problem to a different temp dir
        build = run(["scalac", "-d", outdir, path], timeout_seconds=45)
        if build.exit_code != 0:
            # Well, it's a compile error. May be a type error or
            # something. But, why break the set convention
            return {
                "status": "SyntaxError",
                "exit_code": build.exit_code,
                "stdout": build.stdout,
                "stderr": build.stderr,
            }
        # "Problem" is the name of the class we emit.
        r = run(["scala", "-cp", f"{outdir}", "Problem"])
        if r.timeout:
            status = "Timeout"
        elif r.exit_code == 0 and r.stderr == "":
            status = "OK"
        else:
            # Well, it's a panic
            status = "Exception"
    return {
        "status": status,
        "exit_code": r.exit_code,
        "stdout": r.stdout,
        "stderr": r.stderr,
    }
