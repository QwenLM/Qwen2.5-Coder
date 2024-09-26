# source: https://github.com/openai/human-eval/blob/master/human_eval/execution.py

from typing import Optional, Callable, Dict
from pathlib import Path
import ast
import contextlib
import faulthandler
import io
import os
import multiprocessing
import platform
import signal
import tempfile
import dill

DEFAULT_SANDBOX_DIR = '/tmp/usaco/code_sandbox/sandbox_env.db'
DEFAULT_OUT_FILE = '/tmp/usaco/code_sandbox/sandbox_out.out'

if not os.path.isfile(DEFAULT_SANDBOX_DIR):
    # init empty environment if not available
    Path(DEFAULT_SANDBOX_DIR).parent.mkdir(parents=True, exist_ok=True)
    with open(DEFAULT_SANDBOX_DIR, 'wb') as f:
        dill.dump({}, f)


def run_code(
    code: str,
    timeout: float = 5,
    memory_limit: int = 64,
    out_file: str = DEFAULT_OUT_FILE,
    in_env: str = None,
    out_env: str = None,
) -> str:
    """
    Run code (with time and mem limits), and return string that contains the concatenated stdout
        and stderr. Optional persistent state loading and/or saving are supported and specified
        via in_env and out_env parameters (e.g. to preserve variables or function definitions
        between different calls to run_code).
    in_env: dill environment to read state (e.g. global variables) from
    out_env: dill env to save state to
    """

    f = open(out_file, 'w')  # create file so the read later doesn't fail — file may not be created during exec e.g. if there is a compile issue

    if in_env is not None:
        with open(in_env, 'rb') as f:
            env = dill.load(f)
    elif out_env is not None:
        env = {}

    def unsafe_execute():

        with create_tempdir():

            # These system calls are needed when cleaning up tempdir.
            import os
            import shutil
            rmtree = shutil.rmtree
            rmdir = os.rmdir
            chdir = os.chdir

            # Disable functionalities that can make destructive changes to the test.
            # also sets memory limit
            reliability_guard(memory_limit * 1000000)  # convert MB to bytes

            # Construct the check program and run it.
            prefix_program = f"import sys\nsys.stdout=open('{out_file}', 'w')\n"
            suffix_program = f"\nsys.stdout.close()"
            check_program = prefix_program + code + suffix_program

            # print(check_program)

            try:
                exec_globals = {}
                with swallow_io():
                    with time_limit(timeout):
                        # WARNING
                        # This program exists to execute untrusted model-generated code. Although
                        # it is highly unlikely that model-generated code will do something overtly
                        # malicious in response to this test suite, model-generated code may act
                        # destructively due to a lack of model capability or alignment.
                        # Users are strongly encouraged to sandbox this evaluation suite so that it
                        # does not perform destructive actions on their host or network. For more
                        # information on how OpenAI sandboxes its code, see the accompanying paper.
                        # Once you have read this disclaimer and taken appropriate precautions,
                        # uncomment the following line and proceed at your own risk:
                        if in_env is not None or out_env is not None:
                            exec(check_program, env, env)
                        else:
                            exec(check_program, exec_globals)
            except TimeoutException:
                result.append(f"TimeoutException: Timed out")
            except BaseException as e:
                result.append(f"Exception: {e}")

            # Needed for cleaning up.
            shutil.rmtree = rmtree
            os.rmdir = rmdir
            os.chdir = chdir

            if out_env is not None:
                with open(out_env, 'wb') as f:
                    dill.dump(env, f)

    manager = multiprocessing.Manager()
    result = manager.list()

    p = multiprocessing.Process(target=unsafe_execute)
    p.start()
    p.join(timeout=timeout + 1)
    if p.is_alive():
        p.kill()

    with open(out_file, 'r') as f:
        result.append(f.read().strip())

    return '\n'.join(result)


@contextlib.contextmanager
def time_limit(seconds: float):

    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")

    signal.setitimer(signal.ITIMER_REAL, seconds)
    signal.signal(signal.SIGALRM, signal_handler)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


@contextlib.contextmanager
def swallow_io():
    stream = WriteOnlyStringIO()
    with contextlib.redirect_stdout(stream):
        with contextlib.redirect_stderr(stream):
            with redirect_stdin(stream):
                yield


@contextlib.contextmanager
def create_tempdir():
    with tempfile.TemporaryDirectory() as dirname:
        with chdir(dirname):
            yield dirname


class TimeoutException(Exception):
    pass


class WriteOnlyStringIO(io.StringIO):
    """ StringIO that throws an exception when it's read from """

    def read(self, *args, **kwargs):
        raise IOError

    def readline(self, *args, **kwargs):
        raise IOError

    def readlines(self, *args, **kwargs):
        raise IOError

    def readable(self, *args, **kwargs):
        """ Returns True if the IO object can be read. """
        return False


class redirect_stdin(contextlib._RedirectStream):  # type: ignore
    _stream = 'stdin'


@contextlib.contextmanager
def chdir(root):
    if root == ".":
        yield
        return
    cwd = os.getcwd()
    os.chdir(root)
    try:
        yield
    except BaseException as exc:
        raise exc
    finally:
        os.chdir(cwd)


def reliability_guard(maximum_memory_bytes: Optional[int] = None):
    """
    This disables various destructive functions and prevents the generated code
    from interfering with the test (e.g. fork bomb, killing other processes,
    removing filesystem files, etc.)

    WARNING
    This function is NOT a security sandbox. Untrusted code, including, model-
    generated code, should not be blindly executed outside of one. See the 
    Codex paper for more information about OpenAI's code sandbox, and proceed
    with caution.
    """
    if maximum_memory_bytes is not None:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (maximum_memory_bytes, maximum_memory_bytes))
        resource.setrlimit(resource.RLIMIT_DATA, (maximum_memory_bytes, maximum_memory_bytes))
        if not platform.uname().system == 'Darwin':
            resource.setrlimit(resource.RLIMIT_STACK, (maximum_memory_bytes, maximum_memory_bytes))

    faulthandler.disable()

    import builtins
    builtins.exit = None
    builtins.quit = None

    import os
    os.environ['OMP_NUM_THREADS'] = '1'

    os.kill = None
    os.system = None
    os.putenv = None
    os.remove = None
    os.removedirs = None
    os.rmdir = None
    os.fchdir = None
    os.setuid = None
    os.fork = None
    os.forkpty = None
    os.killpg = None
    os.rename = None
    os.renames = None
    os.truncate = None
    os.replace = None
    os.unlink = None
    os.fchmod = None
    os.fchown = None
    os.chmod = None
    os.chown = None
    os.chroot = None
    os.fchdir = None
    os.lchflags = None
    os.lchmod = None
    os.lchown = None
    os.getcwd = None
    os.chdir = None

    import shutil
    shutil.rmtree = None
    shutil.move = None
    shutil.chown = None

    import subprocess
    subprocess.Popen = None  # type: ignore

    __builtins__['help'] = None

    import sys
    sys.modules['ipdb'] = None
    sys.modules['joblib'] = None
    sys.modules['resource'] = None
    sys.modules['psutil'] = None
    sys.modules['tkinter'] = None
