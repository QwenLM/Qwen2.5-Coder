from pathlib import Path
import datasets
from datetime import datetime
from typing import List, Dict, Any, Tuple, Union, Callable
import pickle

from USACOBench.agents import Agent
from .judges.codeforces_judge import CodeforcesJudge
from .judges.usaco_batch_judge import USACOBatchJudge

Problem = Dict[Any, Any]
Solution = Dict[str, Union[str, None]]
SolutionSet = List[Solution]
Result = Dict[str, str]
ResultSet = List[Result]


# TODO support judge other than codeforces (e.g. usaco, leetcode),
#     in which case maybe add abstract judge class
def evaluate_agent(agent: Agent,
                   problems: Union[datasets.Dataset, List[Problem]],
                   problem_dict: Dict[str, Problem],
                   attempts: int = 10,
                   prompt_fns: List[Callable[..., str]] = None,
                   judge_type: str = 'usaco',
                   return_solution_sets=True,
                   save_solution_sets=True,
                   **kwargs) -> Union[Tuple[List[ResultSet], List[SolutionSet]], List[ResultSet]]:
    '''
    Given an agent and problems, directs the agent to generate solutions,
        then evaluates those solutions using the appropriate judge_type
    '''
    # construct judge sandbox directories if they don't exist
    path = Path('/tmp/usaco/judge_sandbox/solutions/{}/solution_sets/'.format(judge_type))
    path.mkdir(parents=True, exist_ok=True)

    solution_sets = agent.solve(problems, attempts=attempts, prompt_fns=prompt_fns)
    if save_solution_sets:
        timestamp = datetime.now().strftime("%m_%d_%Y_%H_%M_%S_%f")
        fname = '/tmp/usaco/judge_sandbox/solutions/{}/solution_sets/solution_sets_{}.pickle'.format(judge_type, timestamp)
        with open(fname, 'wb') as f:
            pickle.dump(solution_sets, f)
        print('Saved solution sets at {}'.format(fname))
    return evaluate_solution_sets(solution_sets, problem_dict, judge_type, return_solution_sets, **kwargs)


def evaluate_solution_sets(
    solution_sets: List[SolutionSet],
    problem_dict: Dict[str, Problem],
    judge_type: str = 'usaco',
    return_solution_sets=False,
    **kwargs,
) -> Union[Tuple[List[ResultSet], List[SolutionSet]], List[ResultSet]]:
    if judge_type == 'codeforces':
        judge = CodeforcesJudge()
    elif judge_type == 'usaco':
        judge = USACOBatchJudge()
    else:
        assert False, 'Judge {} not supported'.format(judge)

    result_sets = judge.judge(solution_sets, problem_dict, **kwargs)
    if return_solution_sets:
        return result_sets, solution_sets
    return result_sets
