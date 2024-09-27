"""This file checks two things:
1. Is the LLMs codegen completed for each benchmark?
2. Warn the code that are not compilable (it could be some impl issues).
"""

import ast
import traceback

from termcolor import colored

from data import load_solutions


def syntax_check(code, verbose=False):
    try:
        ast.parse(code)
        return True
    except (SyntaxError, MemoryError):
        if verbose:
            traceback.print_exc()
        return False


def script(
    samples: str, nsample_check: int = None, verbose: bool = False
):
    # List[Dict{"task_id", "solution"}]
    solutions = load_solutions(samples)

    from bigcodebench.data import get_bigcodebench

    dataset = get_bigcodebench()
    dataset_name = "BigCodeBench"

    print(colored(f"Dataset: {dataset_name}", "blue"))

    id2solutions = {}
    for solution in solutions:
        task_id = solution["task_id"]
        if task_id not in id2solutions:
            id2solutions[task_id] = []
        if "solution" not in solution:
            assert "completion" in solution, "solution or completion must exist!"
            solution["solution"] = dataset[task_id]["complete_prompt"] + solution["completion"]
        id2solutions[task_id].append(solution)

    print(colored("==============================", "blue"))
    print(colored(" ::: Checking completeness... ", "blue"))
    print(colored(" ::::: All tasks complete?    ", "blue"))
    ndone = 0

    task_ids = dataset.keys()
    ntask = len(task_ids)
    for task_id in task_ids:
        if task_id not in id2solutions:
            print(colored(f" ⚠️ {task_id} is missing!", "red"))
            continue
        nfiles = len(id2solutions[task_id])

        if nsample_check is None or nfiles <= nsample_check:
            ndone += 1
            continue

        print(
            colored(
                f" ⚠️ {task_id} only has {nfiles} samples! But {nsample_check} are expected.",
                "red",
            )
        )

    # check if there is enough number of samples here.
    if nsample_check is not None:
        if ntask != ndone:
            ntbd = ntask - ndone
            print(colored(f" ::::: ⚠️ {ntbd}/{ntask} tasks incomplete!", "red"))
        else:
            print(colored(f" ::::: All {ntask} tasks complete!", "green"))

    print(colored("==============================", "blue"))
    print(colored(" ::: Checking compilation...  ", "blue"))
    print(colored(" ::::: All code compilable?   ", "blue"))
    ncode = 0
    nwrong = 0
    for task_id in task_ids:
        # task_id must exist
        if task_id not in id2solutions:
            continue

        for solution in id2solutions[task_id]:
            ncode += 1
            code = solution["solution"]
            dbg_identifier = solution["_identifier"]
            if code.strip() == "":
                print(colored(f" ⚠️ {dbg_identifier} is empty!", "red"))
                nwrong += 1
            elif not syntax_check(code, verbose):
                print(colored(f" ⚠️ {dbg_identifier} is not compilable!", "red"))
                nwrong += 1
    if 0 != nwrong:
        print(colored(f" ::::: ⚠️ {nwrong}/{ncode} code are not compilable!", "red"))
    else:
        print(colored(f" ::::: All {ncode} code are compilable!", "green"))


def main():
    from fire import Fire

    Fire(script)


if __name__ == "__main__":
    main()
