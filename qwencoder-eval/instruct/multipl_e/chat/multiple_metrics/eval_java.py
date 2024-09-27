import os
import tempfile
from pathlib import Path

from .generic_eval import main
from .safe_subprocess import run

LANG_NAME = "Java"
LANG_EXT = ".java"

# Following files have problems:
# 137,
# 22: Any
# 148: Elipsis


def eval_script(path: Path):

    sys_env = os.environ.copy()
    javatuples_path = Path(f"{os.path.dirname(__file__)}/javatuples-1.2.jar")

    sys_env["CLASSPATH"] = f"{javatuples_path}"

    with tempfile.TemporaryDirectory() as outdir:
        # Each Java file contains the class with same name `JAVA_CLASS_NAME`
        # Hence, javac will same JAVA_CLASS_NAME.class file for each problem
        # Write class for each problem to a different temp dir
        # Use UTF8 encoding with javac
        result = run(["javac", "-encoding", "UTF8", "-d", outdir, path], env=sys_env)

        if result.exit_code != 0:
            # Well, it's a compile error. May be a type error or
            # something. But, why break the set convention
            status = "SyntaxError"
        else:
            result = run(["java", "-ea", "-cp", f"{outdir}", "Problem"], env=sys_env)
            if result.timeout:
                status = "Timeout"
            elif result.exit_code == 0:
                status = "OK"
            else:
                status = "Exception"

    return {
        "status": status,
        "exit_code": result.exit_code,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


if __name__ == "__main__":
    main(eval_script, LANG_NAME, LANG_EXT)
