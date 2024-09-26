# for use inside Jupyter notebook only

import ghdiff
import json
from IPython.display import Markdown

from .utils import get_code_from_solution

def find_prev_code(messages) -> str:
    '''
    Returns the string content of the last code execution message in messages,
        if any. Used for computing the code diff to display for the next message.
    '''
    for i in reversed(range(len(messages))):
        if messages[i]['role'] == 'function' and 'function_call' in messages[i] and messages[i]['content'][:21] != 'Exception encountered' and 'code' in json.loads(messages[i]['function_call']['arguments']): # assumption: every function is preceded by its calling code
            return json.loads(messages[i-1]['function_call']['arguments'])['code']
    return ''

def display_message(message, print_diffs=True, prev_code='', truncate=False):
    '''
    Displays the given message, formatted nicely.
    print_diffs: whether to print GitHub-style diffs instead of the raw code, if any
    prev_code: string of most recent previous code execution, to compute diff
    truncate: whether to truncate long messages (and include full message as collapsible)
    '''
    # print('[[{}]]'.format(message['role'].upper()))
    print('----------------------------------------------------------------------------------------------')
    if 'content' in message and message['content'] is not None:
        if 'role' not in message:
            print('💤 Out of tokens...')
            return
        print(get_emoji(message['role']) + '💬')
        content = message['content']
        if truncate and len(content) > 1000:
            print(content[:1000] + '...\n(message abridged)')
            display(Markdown(long_content_format.format(content)))
        else:
            print(content)
    if 'function_call' in message:
        print('🤖🖥️ Calling {}...'.format(message['function_call']['name']))
        try:
            args = json.loads(message['function_call']['arguments'])
            if 'code' in args:
                print('Code:')
                code = args['code']
                # code = get_code_from_solution(message['function_call']['arguments'])
                if print_diffs:
                    html = diff_format.format(ghdiff.diff(prev_code, code), code)
                    display(Markdown(html))
                else:
                    print(code)
            else:
                for k, v in args.items():
                    print(str(k) + ':')
                    print(v)
        except Exception as e:
            print(e)
            print('[Function call does not json decode]')
            display(Markdown(no_json_decode_format.format(message['function_call'])))
    print()

def display_last_message(messages, print_diffs=True, truncate=False):
    '''
    Displays the last message in the given messsages, formatted nicely.
    print_diffs: whether to print GitHub-style diffs instead of the raw code, if any
    '''
    return display_message(messages[-1], print_diffs=print_diffs, prev_code=find_prev_code(messages[:-1]), truncate=truncate)

def display_messages(messages, print_diffs=True, truncate=False):
    '''
    Displays the given message formatted nicely.
    print_diffs: whether to print GitHub-style diffs instead of the raw code, if any
    '''
    for i, message in enumerate(messages):
        if print_diffs:
            display_message(message, print_diffs=print_diffs, prev_code=find_prev_code(messages[:i]), truncate=truncate)
        else:
            display_message(message, print_diffs=print_diffs, truncate=truncate)

# various utilities and formats for pretty printing
def get_emoji(role):
    if role == 'assistant':
        return '🤖'
    elif role == 'user':
        return '👩‍🦲'
    elif role == 'function':
        return '🖥️'
    else:
        return '❓'

diff_format = '''
{}
<details>
<summary>Show full code</summary>

```python
{}
```

</details>
'''

no_json_decode_format = '''
<details>
<summary>Show invalid json</summary>

```
{}
```

</details>
'''

long_content_format = '''
<details>
<summary>Show full message</summary>

```
{}
```

</details>
'''
