from pathlib import Path
import numpy as np
import time
from datetime import datetime
import random
import subprocess
from typing import List, Dict, Any, Union

from .codeforces_utils import parse_codeforces_result_type
from .judge import Judge

Problem = Dict[Any, Any]
Solution = Dict[str, Union[str, None]]
SolutionSet = List[Solution]
Result = Dict[str, str]
ResultSet = List[Result]

# [README] modify solutions path
CODEFORCES_SOLUTIONS_PATH = '/tmp/usaco/judge_sandbox/solutions/codeforces/{}_{}_{}.py'
# construct judge sandbox directories if they don't exist
Path('/tmp/usaco/judge_sandbox/solutions/codeforces').mkdir(parents=True, exist_ok=True)


class CodeforcesJudge(Judge):

    def __init__(self, solutions_path: str = CODEFORCES_SOLUTIONS_PATH, sleep_length: float = 2):
        '''
        solutions_path: filepath for auxiliary solution files to be created
            and stored (cf-tool reads from file)
        sleep_length: amount to sleep after each submission to avoid
            rate limit (if None, random amount between 0-1 seconds)
        '''
        super().__init__(solutions_path, sleep_length)

    # TODO support non-py solutions (need to update submission language)
    # TODO support codeforces gym problems
    def _judge(self, problem: Problem, solution_code: str, language: str = 'Python3') -> Result:
        assert 'cf_contest_id' in problem and 'cf_index' in problem, 'Need contest id and index to judge Codeforces problem'
        assert language == 'Python3', 'Only Python 3 is supported'
        if solution_code is None:
            return {'result_type': ResultType.UNKNOWN, 'status': 'No submission', 'judge_output': 'No submission'}
        return self._codeforces_python3_judge(solution_code, problem['cf_contest_id'], problem['cf_index'])

    def _codeforces_python3_judge(self, solution_code: str, cf_contest_id: int, cf_index: str) -> Result:
        '''
        Judges a Python3 Codeforces solution; returns result as a
            dictionary with status and judge_output strings
        solution_code: code to submit as a string
        cf_contest_id: contest, e.g. 1136
        cf_index: problem, e.g. A
        '''
        timestamp = datetime.now().strftime("%m_%d_%Y_%H_%M_%S_%f")
        solution_file = self.solutions_path.format(cf_contest_id, cf_index, timestamp)
        # append timestamp to avoid 'You have submitted exactly the same code before' error
        timestamp_prefix = '# Timestamp: {}\n\n'.format(timestamp)
        with open(solution_file, 'w') as f:
            f.write(timestamp_prefix + solution_code)
        output = subprocess.run(['bash', 'cf_tool/submit.sh', str(cf_contest_id), str(cf_index), timestamp], capture_output=True)
        judge_output = output.stdout.decode()
        status = self._codeforces_parse_status(judge_output)
        return {
            'result_type': parse_codeforces_result_type(status),
            'status': status,
            'judge_output': judge_output,
            'solution_file': solution_file,
        }

    # TODO status should be a struct, not a string
    # TODO parse other metadata like the test it failed on,
    #     for judges / envs where this is available
    def _codeforces_parse_status(self, judge_output: str) -> str:
        '''
        judge_output: cf-tool output string
        Returns status (e.g. 'Accepted', 'Wrong answer', etc)
        '''
        status_delim = 'status: '
        status_begin_idx = judge_output.rfind(status_delim) + len(status_delim)
        status_end_idx = judge_output.index('\n', status_begin_idx)
        return judge_output[status_begin_idx:status_end_idx]
