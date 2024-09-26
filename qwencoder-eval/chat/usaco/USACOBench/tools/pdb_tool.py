import sys
import time
from datetime import datetime
import subprocess
from functools import partial
import multiprocessing
from multiprocessing import Queue
from copy import deepcopy

import threading

# TODO deal with stderr

def iterate_stdout(process, cmd):
    '''
    Behaves as a char-by-char generator for process stdout
    '''
    for stdout_char in iter(lambda: process.stdout.read(1), b""):
        yield stdout_char
    process.stdout.close()
    return_code = process.wait()
    if return_code:
        # raise subprocess.CalledProcessError(return_code, cmd)
        yield subprocess.CalledProcessError(return_code, cmd)

def iterate_stderr(process, cmd):
    '''
    Behaves as a char-by-char generator for process stderr
    '''
    for stdout_char in iter(lambda: process.stderr.read(1), b""):
        yield stdout_char
    process.stdout.close()
    return_code = process.wait()
    if return_code:
        # raise subprocess.CalledProcessError(return_code, cmd)
        yield subprocess.CalledProcessError(return_code, cmd)

def catch_stdout(process, outputs, cmd):
    '''
    Catches process stdout line-by-line and adds it to lst
    '''
    for out in iterate_stdout(process, cmd):
        outputs.put(out)

def catch_stderr(process, outputs, cmd):
    '''
    Catches process stderr line-by-line and adds it to lst
    '''
    for out in iterate_stderr(process, cmd):
        outputs.put(out)

# time between input and output, to interact with subprocess
# TODO more robust way to do this
FLUSH_TIME = 0.1

class DebugSession:
    '''
    Represents an interactive pdb debug session on a Python
    script. You can construct a new sesssion given a piece of
    code, then step in the session by sending in new stdin inputs,
    receiving new stdout outputs, and finally exit.
    '''
    def __init__(self,
                 code,
                 session_name: str = 'session'):
        timestamp_str = datetime.now().strftime("%m_%d_%Y_%H_%M_%S_%f")
        code_fname = 'code_sandbox/code_{}_{}.py'.format(session_name, timestamp_str)
        code = 'import pdb; pdb.set_trace()\n' + code
        with open(code_fname, 'w') as f:
            f.write(code)
        cmd = [sys.executable, '-u', code_fname]
        self.exec_process = subprocess.Popen(cmd,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   universal_newlines=True,
                                   text=True)
        self.output_buffer = Queue()
        self.transcript = []
        catch_stdout_fn = partial(catch_stdout, self.exec_process, self.output_buffer, cmd)
        catch_stderr_fn = partial(catch_stderr, self.exec_process, self.output_buffer, cmd)
        self.catch_stdout_process = multiprocessing.Process(target=catch_stdout_fn)
        self.catch_stderr_process = multiprocessing.Process(target=catch_stderr_fn)
        # self.catch_process = threading.Thread(target=catch_output_fn)
        self.catch_stdout_process.start()
        self.catch_stderr_process.start()

    def get_output(self) -> str:
        outs = []
        while not self.output_buffer.empty():
            outs.append(self.output_buffer.get())
        output = ''.join(outs)
        if len(output) > 0:
            self.transcript.append({'role': 'terminal', 'content': output})
        # self.output_buffer.clear()
        return output

    def has_output(self) -> bool:
        return len(self.output_buffer) > 0

    def get_transcript(self):
        '''
        Get transcript, a list of dictionaries of all user inputs and
        debugger outputs with role and content keys, in chronological order.
        '''
        return self.transcript

    def send_input(self, input: str):
        '''
        Interact with new input (str), receiving new output (str)
        '''
        # send input
        self.exec_process.stdin.write(input)
        self.exec_process.stdin.flush()
        self.transcript.append({'role': 'user', 'content': input})

    def end(self):
        '''
        Permanently end session
        '''
        self.exec_process.kill()
        self.catch_stdout_process.kill()
        self.catch_stderr_process.kill()
        self.transcript.append({'role': 'user', 'content': 'Ended session'})

# dictionary of (session_name, DebugSession)
sessions = {} # currently open sessions
# dictionary of (session_name+timestamp, transcript string)
transcripts = {} # transcripts of ended sessions

# session monitoring utils
def print_session_statuses():
    print('Session process aliveness:')
    for key, sess in sessions.items():
        print('Session {}: exec process alive? [{}], stdout catch process alive? [{}], stderr catch process alive? [{}]'.format(key, sess.catch_stdout_process.is_alive(), sess.catch_stderr_process.is_alive(), sess.exec_process.poll() is None))

def get_sessions():
    return sessions

def get_transcripts():
    return transcripts

# agent tool usage utils
def debug_init(session_name, code) -> str:
    '''
    Returns a string describing success or failure
    '''
    if session_name in sessions:
        return 'Session name {} already in use'.format(session_name)
    sessions[session_name] = DebugSession(code, session_name)
    time.sleep(FLUSH_TIME)
    # return 'DONE'
    return 'Started new pdb debugging session with session_name={}\n{}'.format(session_name, sessions[session_name].get_output())

def debug_interact(session_name, input: str) -> str:
    '''
    Interact with session session_name, with new input (str),
    receiving new output (str)
    '''
    if session_name not in sessions:
        return 'Session name {} not found. Did you initialize it?'.format(session_name)
    try:
        session = sessions[session_name]
        session.send_input(input)
        time.sleep(FLUSH_TIME)
        return session.get_output()
    except Exception as e:
        return 'Exception: {}'.format(e)

def debug_end(session_name):
    '''
    Permanently end session and remove from session list
    '''
    if session_name not in sessions:
        return 'Session name {} not found.'.format(session_name)
    sessions[session_name].end()
    sessions.pop(session_name)
    return 'Ended session with session_name={}, removed from list of current sessions\n'.format(session_name)

# for debug
def get_transcript(session_name):
    if session_name not in sessions:
        return 'Session name {} not found.'.format(session_name)
    return sessions[session_name].get_transcript()
