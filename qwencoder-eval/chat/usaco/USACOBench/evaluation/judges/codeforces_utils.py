from USACOBench.evaluation.result_type import ResultType

def parse_codeforces_result_type(status: str) -> ResultType:
    status = status.lower()
    if 'accepted' in status:
        return ResultType.ACCEPTED
    if 'wrong answer' in status or 'incorrect' in status:
        return ResultType.WRONG_ANSWER
    if 'time limit exceeded' in status or 'tle' in status:
        return ResultType.TIME_LIMIT_EXCEEDED
    if 'memory limit exceeded' in status or 'memory error' in status:
        return ResultType.MEMORY_LIMITED_EXCEEDED
    if 'compilation error' in status:
        return ResultType.COMPILATION_ERROR
    if 'runtime error' in status:
        return ResultType.RUNTIME_ERROR
    return ResultType.UNKNOWN