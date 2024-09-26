from typing import Any, List, Dict, Union
import json

from USACOBench.utils import get_code_from_solution
from .sandbox import run_code, DEFAULT_SANDBOX_DIR
from .pdb_tool import debug_init, debug_interact, debug_end

# no saved state
def run_code_wrapper(code):
    return run_code(code)

# with saved state
# def run_code_wrapper(code):
#     return run_code(code, in_env=DEFAULT_SANDBOX_DIR, out_env=DEFAULT_SANDBOX_DIR)

# for testing
def mock_run_code(code=None):
    assert code is not None
    output = {
        'output': 'Hello World',
        # TODO maybe separate stdout and stderr, add exit status, tracebacks, etc
    }
    return json.dumps(output)

'''
tools: list of tool specifications, each of which contains a name, description, and parameter info to be added
    to the prompt. The prompting details are abstracted out and handled by the OpenAI API backend.
'''
tools = [
#     {
#         "name": "run_code",
#         "description": '''Runs Python 3 code, and returns the concatenated stdout and stderr as a string. Remember that:
# (1) Wrap 'print()' around all desired outputs. Only the stdout and stderr will be returned (e.g. this is not a shell or IPython, raw return values will not be returned).
# (2) No outside libraries are supported.''',
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "code": {
#                     "type": "string",
#                     "description": "Python 3 code", # Code wrapped in '```python' and '```' delimiters
#                 },
#             },
#             "required": ["code"],
#         },
#     },
    {
        "name": "debug_init",
        "description": '''Begin an interactive debug session. Must be called before debug_interact. Adds 'import pdb; pdb.set_trace()' to the beginning of the given code to initiate the debugger. Recall that (pdb) is usually a pdb command prompt, and a newline is usually a stdin prompt.''',
        "parameters": {
            "type": "object",
            "properties": {
                "session_name": {
                    "type": "string",
                    "description": "Unique identifier for the name of the debug session (each call to init_debug requires a different identifier)", # Code wrapped in '```python' and '```' delimiters
                },
                "code": {
                    "type": "string",
                    "description": "Python 3 code", # Code wrapped in '```python' and '```' delimiters
                },
            },
            "required": ["session_name", "code"],
        },
    },
    {
        "name": "debug_interact",
        "description": '''Interact with an initialized pdb debug session. Send in input, receive output. Standard pdb syntax.  Recall that (pdb) is usually a pdb command prompt, and a newline is usually a stdin prompt.''',
        "parameters": {
            "type": "object",
            "properties": {
                "session_name": {
                    "type": "string",
                    "description": "Unique identifier for the name of the debug session (same as the one in the respective call to debug_init)", # Code wrapped in '```python' and '```' delimiters
                },
                "input": {
                    "type": "string",
                    "description": "pdb or code input, should end with newline character", # Code wrapped in '```python' and '```' delimiters
                },
            },
            "required": ["session_name", "input"],
        },
    },
    {
        "name": "debug_end",
        "description": '''Permanently end initialized pdb debug session. Should do after finishing debugging if the program was not allowed to run fully, to prevent hanging threads.''',
        "parameters": {
            "type": "object",
            "properties": {
                "session_name": {
                    "type": "string",
                    "description": "Unique identifier for the name of the debug session (same as the one in the respective call to debug_init)", # Code wrapped in '```python' and '```' delimiters
                },
            },
            "required": ["session_name"],
        },
    },
]

'''
tool_dict: dictionary from tool name string to callable tool function
'''
tool_dict = {
    # "run_code": run_code_wrapper,
    'debug_init': debug_init,
    'debug_interact': debug_interact,
    'debug_end': debug_end,
}

def invoke_tool(message: Dict[str, Any],
                tool_dict: Dict[str, Any]):
    '''
    Given a message that invokes a tool in the given tool_dict, return the resulting message
        from the tool (if the invocation is improperly formatted, returns an error message)
    '''
    # TODO support arguments for non-code tools
    # Note: the JSON response may not always be valid
    try:
        # parse invocation
        function_name = message["function_call"]["name"]
        function_to_call = tool_dict[function_name]
        # code = get_code_from_solution(message["function_call"]["arguments"]) # Markdown parsing is more reliable than JSON due to
        # the nested string formatting issue with JSON (e.g. code inside tool JSON inside message JSON)
        function_args = json.loads(message["function_call"]["arguments"])
        # code = function_args['code']

        # invoke and return response
        function_response = function_to_call(**function_args)
        # if not function_response:
        #     function_response = '\nEmpty stdout. Did you remember to print desired outputs to stdout using e.g. print()?'
        return {
            "role": "function",
            "name": function_name,
            "content": function_response,
        }
    except Exception as e:
        return {
            "role": "function",
            "name": function_name,
            # "content": 'Invalid function call. Make sure to input valid Python 3 code as a string, with the desired outputs printed to stdout. Exception encountered: {}'.format(e),
            "content": 'Exception encountered:\n{}'.format(e),
        }
