"""
NOTE: Nothing containerized about this any more. This is just a helper
for problem_evaluator.py.
"""

import tempfile
from pathlib import Path

from . import (eval_cpp, eval_dlang, eval_java, eval_javascript, eval_julia,
               eval_lua, eval_php, eval_python, eval_r, eval_racket, eval_ruby,
               eval_rust, eval_swift, eval_ts, eval_go, eval_pl, eval_sh, eval_scala, eval_cs)

EVALUATORS = {
    "rb": (eval_ruby.eval_script, ".rb"),
    "lua": (eval_lua.eval_script, ".lua"),
    "python": (eval_python.eval_script, ".py"),
    "py": (eval_python.eval_script, ".py"),
    "notypes.py": (eval_python.eval_script, ".py"),
    "julia": (eval_julia.eval_script, ".jl"),
    "java": (eval_java.eval_script, ".java"),
    "rust": (eval_rust.eval_script, ".rs"),
    "rs": (eval_rust.eval_script, ".rs"),
    "swift": (eval_swift.eval_script, ".swift"),
    "lua": (eval_lua.eval_script, ".lua"),
    "racket": (eval_racket.eval_script, ".rkt"),
    "rkt": (eval_racket.eval_script, ".rkt"),
    "javascript": (eval_javascript.eval_script, ".js"),
    "js": (eval_javascript.eval_script, ".js"),
    "cpp": (eval_cpp.eval_script, ".cpp"),
    "cs": (eval_cs.eval_script, ".cs"),
    "php": (eval_php.eval_script, ".php"),
    "humaneval_to_dlang.py": (eval_dlang.eval_script, ".d"),
    "d": (eval_dlang.eval_script, ".d"),
    "r": (eval_r.eval_script, ".r"),
    "humaneval_to_r.py": (eval_r.eval_script, ".r"),
    "jl": (eval_julia.eval_script, ".jl"),
    "ts": (eval_ts.eval_script, ".ts"),
    "go": (eval_go.eval_script, ".go"),
    "pl": (eval_pl.eval_script, ".pl"),
    "sh": (eval_sh.eval_script, ".sh"),
    "scala": (eval_scala.eval_script, ".scala"),
}


def eval_string_script(language, program):
    if language in EVALUATORS:
        (eval_script, file_ext) = EVALUATORS[language]
    else:
        eval_module = __import__(
            f"eval_{language}" if language != "go_test.go" else "eval_go"
        )
        eval_script = eval_module.eval_script
        file_ext = f".{language}" if language != "go_test.go" else "_test.go"
    with tempfile.NamedTemporaryFile(suffix=file_ext, delete=True) as f:
        f.write(program.encode("utf-8"))
        f.flush()
        result = eval_script(Path(f.name))
        # Only save the first 2K of output from the running program. Any futher
        # output is very likely an exceptionally long stack trace or a long
        # series of prints.
        if type(result["stdout"]) == bytes:
            result["stdout"] = result["stdout"].decode("utf-8", errors="ignore")
        if result["stdout"] is None:
            result["stdout"] = ""
        if result["stderr"] is None:
            result["stderr"] = ""
        if type(result["stderr"]) == bytes:
            result["stderr"] = result["stderr"].decode("utf-8", errors="ignore")
        assert type(result["stdout"]) == str
        assert type(result["stderr"]) == str
        return {
            "program": program,
            "stdout": result["stdout"].replace("!!int", "")[:2048],
            "stderr": result["stderr"][:2048],
            "exit_code": result["exit_code"],
            "status": result["status"],
        }
