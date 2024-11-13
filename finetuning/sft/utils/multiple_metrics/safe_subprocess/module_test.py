import time
from pathlib import Path

from safe_subprocess import run

ROOT = Path(__file__).resolve().parent / "evil_programs"


def assert_no_running_evil():
    result = run(["pgrep", "-f", ROOT], timeout_seconds=1, max_output_size=1024)
    assert (
        result.exit_code == 1
    ), f"There are still evil processes running: {result.stdout}"
    assert len(result.stderr) == 0
    assert len(result.stdout) == 0


def test_fork_once():
    # The program exits cleanly and immediately. But, it forks a child that runs
    # forever.
    result = run(
        ["python3", ROOT / "fork_once.py"],
        timeout_seconds=2,
        max_output_size=1024,
    )
    assert result.exit_code == 0
    assert result.timeout == False
    assert len(result.stderr) == 0
    assert len(result.stdout) == 0
    assert_no_running_evil()


def test_close_outputs():
    # The program prints to stdout, closes its output, and then runs forever.
    result = run(
        ["python3", ROOT / "close_outputs.py"],
        timeout_seconds=2,
        max_output_size=1024,
    )
    assert result.exit_code == -1
    assert result.timeout == True
    assert len(result.stderr) == 0
    assert result.stdout == "This is the end\n"
    assert_no_running_evil()


def test_unbounded_output():
    result = run(
        ["python3", ROOT / "unbounded_output.py"],
        timeout_seconds=3,
        max_output_size=1024,
    )
    assert result.exit_code == -1
    assert result.timeout == True
    assert len(result.stderr) == 0
    assert len(result.stdout) == 1024
    assert_no_running_evil()


def test_sleep_forever():
    result = run(
        ["python3", ROOT / "sleep_forever.py"],
        timeout_seconds=2,
        max_output_size=1024,
    )
    assert result.exit_code == -1
    assert result.timeout == True
    assert len(result.stderr) == 0
    assert len(result.stdout) == 0
    assert_no_running_evil()


def test_fork_bomb():
    result = run(
        ["python3", ROOT / "fork_bomb.py"],
        timeout_seconds=2,
        max_output_size=1024,
    )
    assert result.exit_code == -1
    assert result.timeout == True
    assert len(result.stderr) == 0
    assert len(result.stdout) == 0
    # Unfortunately, this sleep seems to be necessary. My theories:
    # 1. os.killpg doesn't block until the whole process group is dead.
    # 2. pgrep can produce stale output
    time.sleep(2)
    assert_no_running_evil()


def test_block_on_inputs():
    # We run the subprocess with /dev/null as input. So, any program that tries
    # to read input will error.
    result = run(
        ["python3", ROOT / "block_on_inputs.py"],
        timeout_seconds=2,
        max_output_size=1024,
    )
    assert result.exit_code == 1
    assert result.timeout == False
    assert len(result.stdout) == 0
    assert "EOF when reading a line" in result.stderr
    assert_no_running_evil()
