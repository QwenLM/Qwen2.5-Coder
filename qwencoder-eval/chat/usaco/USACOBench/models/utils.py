from typing import Any, List, Dict, Union

def is_finished(messages: List[Dict[str, Any]]) -> bool:
    '''
    Whether to stop generating in a conversation, i.e. whether (1) no role in last messaeg
        (indicates out of tokens) or last message was the assistant
    '''
    return 'role' not in messages[-1] or messages[-1]['role'] == 'assistant'
