from pathlib import Path
from typing import List, Dict, Any, Tuple, Union, Callable
import pickle
import os
import sys
from datetime import datetime
from typing import Dict, List
from functools import partial
import time

from USACOBench.utils import get_code_from_solution

Problem = Dict[Any, Any]
Solution = Dict[str, Union[str, None]]
SolutionSet = List[Solution]
SolutionDict = Dict[str, SolutionSet]
Result = Dict[str, str]
ResultSet = List[Result]
ResultDict = Dict[str, ResultSet]
Query = Dict[str, str]


def judge_fn_solve(responses: List[str], queries: List[Query], verbose=False) -> List[Result]:
    '''
    Result is the USACO judge outcome (ACCEPTED, WRONG_ANSWER, etc) based on final code.
    Expects code in the Markdown format as defined in iml.utils.get_code_from_solution
    '''
    solution_sets = [[{
        'problem_id': query['problem_id'],
        'solution': response,
        'solution_code': get_code_from_solution(response),
        'language': 'Python3',
    }] for query, response in zip(queries, responses)]
    results = evaluate_ss(solution_sets, mode='eval_all')
    return [result[0] for result in results]  # flatten


def evaluate_model(model_fn: Callable, prompt_fn: Callable, queries: List[Query], attempts: int, problem_ids: List[str] = None, verbose=False) -> Tuple[ResultDict, SolutionDict, List[ResultSet], List[SolutionSet]]:
    '''
    model_fn: takes in list of string prompts and outputs list of string responses, supports verbose bool
    prompt_fn: returns a prompt string: takes in a query, which is a dict of strings
    queries: list of queries to evaluate containing information to be inputted into the prompt function
    problem_ids: we evaluate only on query-ground truth pairs with problem_ids in this list. If None, all problem_ids are valid.
    attempts: number of times to run each query
    '''
    # queries, grond truths, prompts
    if problem_ids is not None:
        problem_ids = set(problem_ids)
        valid_idxs = [idx for idx, query in enumerate(queries) if query['problem_id'] in problem_ids]
        if verbose:
            print('Evaluating on a subset of {} out of {} available query-ground_truth pairs...'.format(len(valid_idxs), len(queries)))
        queries = [queries[idx] for idx in valid_idxs]
    prompt_fns = [prompt_fn] * len(queries)
    if verbose:
        print('Evaluating on {} queries...'.format(len(queries)))

    # model and judge
    model_fn = partial(model_fn, verbose=verbose)
    judge_fn = partial(judge_fn_solve, verbose=verbose)

    prompts = [prompt_fn(query) for prompt_fn, query in zip(prompt_fns, queries)] * attempts
    if verbose:
        print('Generating...')
        start_time = time.time()
    responses = model_fn(prompts, temperature=0.0)
    if verbose:
        print('Finished generation, took {} seconds'.format(time.time() - start_time))

    if verbose:
        print('Judging...')
        start_time = time.time()
    results = judge_fn(responses, queries * attempts)
    if verbose:
        print('Finished judging, took {} seconds'.format(time.time() - start_time))

    # nicer result formats
    rdict = {}
    for result in results:
        problem_id = result['problem_id']
        if problem_id not in rdict:
            rdict[problem_id] = []
        rdict[problem_id].append(result)
    rs = list(rdict.values())

    # nicer solution formats
    # note: this sdict / ss includes the result for easier qualitative eval, so may be slightly bulkier
    # no ground truth, e.g. code
    sdict = {}
    for solution, prompt, query in zip(responses, prompts, queries):
        problem_id = query['problem_id']
        matching_result = None
        for result in results:
            if result['problem_id'] == problem_id:
                matching_result = result
                break

        if problem_id not in sdict:
            sdict[problem_id] = []
        sdict[problem_id].append({
            'solution': solution,
            'solution_code': get_code_from_solution(solution),
            'result': matching_result,
            'problem_id': problem_id,
            'prompt': prompt,
        })
    ss = list(sdict.values())

    return rdict, sdict, rs, ss


def evaluate_ss(ss, mode='eval_all') -> List[ResultSet]:
    '''
    Returns result sets for the given solution sets. For use inside Jupyter environments,
        where directly calling evaluate_solution_sets crashes the environment. Uses os.system instead.
    Returns a list of result sets.
    '''
    timestamp_str = datetime.now().strftime("%m_%d_%Y_%H_%M_%S_%f")
    with open('/tmp/usaco/judge_sandbox/solution_sets_{}.pickle'.format(timestamp_str), 'wb') as f:
        pickle.dump(ss, f)
    os.system(f"{sys.executable} evaluate_solution_sets.py -s /tmp/usaco/judge_sandbox/solution_sets_{timestamp_str}.pickle -r /tmp/usaco/judge_sandbox/result_sets_{timestamp_str}.pickle -m {mode}")
    try:
        with open('/tmp/usaco/judge_sandbox/result_sets_{}.pickle'.format(timestamp_str), 'rb') as f:
            rs = pickle.load(f)
    except Exception as error:
        print(error)
        return None
    return rs


def evaluate_code(problem_id, code) -> Result:
    '''
    Evaluates given code for problem problem_id on all test cases and returns results.
        For use inside Jupyter environments.
    Returns a single result.
    '''
    timestamp_str = datetime.now().strftime("%m_%d_%Y_%H_%M_%S_%f")
    with open('/tmp/usaco/judge_sandbox/code_{}.py'.format(timestamp_str), 'w') as f:
        f.write(code)
    os.system('python usaco_judge_one.py /tmp/usaco/judge_sandbox/code_{}.py -i {} -r --result_path /tmp/usaco/judge_sandbox/result_{}.pickle'.format(timestamp_str, problem_id, timestamp_str))
    with open('/tmp/usaco/judge_sandbox/result_{}.pickle'.format(timestamp_str), 'rb') as f:
        result = pickle.load(f)
    return result


def run_code_on_input(problem_id, code, input) -> str:
    '''
    Evaluates given code for problem problem_id on the given input and returns the printed output.
        For use inside Jupyter environments.
    Returns an output string.
    '''
    timestamp_str = datetime.now().strftime("%m_%d_%Y_%H_%M_%S_%f")
    code_prefix = '''import sys;sys.stdout = open('output_{}.txt', 'w');sys.stderr = sys.stdout\n'''.format(timestamp_str)
    code = code_prefix + code
    with open('/tmp/usaco/judge_sandbox/code_{}.py'.format(timestamp_str), 'w') as f:
        f.write(code)
    with open('/tmp/usaco/judge_sandbox/input_{}.txt'.format(timestamp_str), 'w') as f:
        f.write(input)
    os.system('cat /tmp/usaco/judge_sandbox/input_{}.txt | python /tmp/usaco/judge_sandbox/code_{}.py'.format(timestamp_str, timestamp_str))
    with open('output_{}.txt'.format(timestamp_str), 'r') as f:
        output = f.read()
    return output


def run_code_on_first_sample(problem, code, return_all=False, print_all=True):
    '''
    Evaluates given code for problem problem_id on the first sample, if available,
        and returns the printed output. For use inside Jupyter environments.
    Returns an output string.
    return_all: returns not just output but (output, input, expected_output)
    '''
    problem_id = problem['problem_id']
    assert 'samples' in problem and len(problem['samples']) > 0, 'No samples found'
    input = problem['samples'][0]['input']
    expected_output = problem['samples'][0]['output']
    output = run_code_on_input(problem['problem_id'], code, input)

    if print_all:
        print('Input:')
        print(input.strip())
        print()
        print('Output:')
        print(output.strip())
        print()
        print('Expected output:')
        print(expected_output.strip())
        print()
    if return_all:
        return output.strip(), input.strip(), expected_output.strip()
    return output
