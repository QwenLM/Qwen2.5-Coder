# Copyright (c) Meta Platforms, Inc. and affiliates.

import sys
print(sys.version_info)
assert (3, 7, 0) < sys.version_info < (3, 10), 'ByteCode is not very stable and may change across python versions. The actual filtering was done on Python 3.9'

import opcode
import dis
import get_stack
import traceback
from collections import Counter
import signal
import ast

bad = Counter() 
numsteps = 0
MAX_STEPS = 100000
NUM_TYPES = [int, float]
LIST_TYPES = [list, str]

class TimeoutException(Exception): pass
class ForbiddenException(Exception): pass

whitelist = []

# trace is explained well here: https://explog.in/notes/settrace.html
def filter_trace(frame, event, arg, verbose=0):
    global bad, numsteps
    frame.f_trace_opcodes = True
    code = frame.f_code
    offset = frame.f_lasti
    numsteps += 1

    if numsteps > MAX_STEPS:
       sys.settrace(None)
       bad['MAX_STEPS'] = 1
       return None
    
    # print('event', event, f"{str(arg):>4}")
    # if event == 'exception':
    #     sys.settrace(None)
    #     # a bit wrong to filter, since some exceptions are part of normal execution.
    #     bad['EXCEPTION'] += 1
    #     return None

    opname = opcode.opname[code.co_code[offset]]
    
    def print_trace():
        print(f"| {event:10} | {str(arg):>4} |", end=' ')
        print(f"{frame.f_lineno:>4} | {frame.f_lasti:>6} |", end=' ')
        print(f"{opname:<18}", end=' ')
        if opname in whitelist or opname.startswith('BINARY_'):
            opstack = get_stack.OpStack(frame)
            print(opstack, end=' ')
        print()
        # print(f"{str(frame.f_locals):<35} |")
    if verbose > 1:
        print_trace()

    if opname.startswith('BINARY_') or opname.startswith('INPLACE_'):
        opstack = get_stack.OpStack(frame)
        # print(opname, opstack)
        if opstack and len(opstack) >= 2:
            o1, o2 = opstack[-1], opstack[-2]
            if type(o1) in NUM_TYPES and type(o2) in NUM_TYPES:
                if abs(o1) > 3 and abs(o2) > 3:
                    bad['OPS_BIG'] += 1
                    # print_trace()
                if opname.endswith('_POWER') and abs(o2) > 1:
                    bad['POWER_BIG'] += 1
                if opname.endswith('_TRUE_DIVIDE'):
                    bad['TRUE_DIVIDE'] += 1
                if type(o1) == float or type(o2) == float:
                    bad['FLOAT_OPS'] += 1
                    # print_trace()
            if type(o1) in LIST_TYPES and type(o2) in LIST_TYPES:
                if len(o1) > 3 and len(o2) > 3:
                    bad['OPS_LONG'] += 1
                    # print_trace()

    return lambda frame, event, arg: filter_trace(frame, event, arg, verbose=verbose)

def check_assert(assert_line):
    # assert f(no_f) = literal
    b = ast.parse(assert_line).body[0]
    if not(type(b) == ast.Assert
        and type(b.test) == ast.Compare
        and type(b.test.left) == ast.Call
        and type(b.test.left.func) == ast.Name
        and b.test.left.func.id == 'f'
        and len(b.test.comparators) == 1):
        return False
    
    # output is a literal
    literal_types = [ast.Constant, ast.List, ast.Tuple, ast.Set, ast.Dict, ast.Load, ast.UnaryOp, ast.USub]
    output = b.test.comparators[0]
    for node in ast.walk(output):
        if type(node) not in literal_types:
            return False
    
    # input should not call f again
    inputs = b.test.left.args
    for arg in inputs:
        for node in ast.walk(arg):
            if type(node) == ast.Call and type(node.func) == ast.Name and type(node.func.id) == 'f':
                print(ast.dump(node))
                return False

    return True

def annotate(code, timeout=2, verbose=0):
    global bad, numsteps
    bad = Counter()
    numsteps = 0
    num_ins = 0

    # Filters to remove undesirable code before executing
    # This does not make execution completely safe
    try:
        if not code.replace('\t', '').replace('\n', '').isprintable():
            raise ForbiddenException('NOT_PRINTABLE')

        forbid = ['import ', '__builtins__', '__builtin__', 'globals()', 'open(', 'exec(', 'eval('] + \
            ['input(', 'hash(', 'set(', 'locals()'] # undesirable
        
        for f in forbid:
            if f in code:
                raise ForbiddenException(f)
        ins = list(dis.get_instructions(compile(code, '<string>', 'exec', optimize=0)))
        num_ins = len(ins)
        # if verbose > 0:
        #     print(dis.dis(code))
        for i in ins:
            if i.opname == 'IMPORT_NAME':
                bad['IMPORT_NAME'] += 1
        
        last_line = code.strip().split('\n')[-1]
        if not check_assert(last_line):
            raise ForbiddenException('Improper Assert: ' + last_line)

    except SyntaxError as e:
        bad['SyntaxError'] += 1
        bad[e] += 1
    except ForbiddenException as e:
        bad[e] += 1

    if len(bad) > 0:
        return {'num_ins': num_ins, 'bad': bad}

    ## Fine on syntax, now do runtime filters
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(timeout)

    try:
        sys.settrace(lambda frame, event, arg: filter_trace(frame, event, arg, verbose=verbose))
        scope = {} # specifying scope is necessary for nested functions 
        exec(compile(code, '<string>', 'exec', optimize=0), scope, scope)
    except TimeoutException as e:
        sys.settrace(None)
        bad['TIMED_OUT'] += 1
        # print(code)
    except Exception as e:
        sys.settrace(None)
        if verbose > 1:
            traceback.print_exc() 
        bad['UNCAUGHT_EXCEPTION'] += 1
    finally:
        sys.settrace(None)
        signal.alarm(0)
        
    return {'num_ins': num_ins, 'bad': bad, 'numsteps': numsteps}


def test():
    code1 = """
def f(number, separator):
    gmd = ((2**100)-1)**3
    text = ''
    while number:
        number, rem = divmod(number,gmd)
        text = hex(rem)[2::].zfill(3) + separator + text
    return text
assert f(27831+3949*72, '@') == '4c35f@'
    """
    code2 = """
def f(a, b, c):
    a += b
    a.clear()
    return a
assert f([], [1], [2]) == []
"""

    res = annotate(code1, verbose=1)
    print(res)
    assert len(res['bad']) > 0

    res = annotate(code2, verbose=1)
    print(res)
    assert len(res['bad']) == 0

if __name__ == "__main__":
    test()
