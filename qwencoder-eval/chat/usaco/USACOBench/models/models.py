import numpy as np
import tiktoken
from typing import Any, List, Dict, Union

from .gpt import gpts, chatgpts_raw
from USACOBench.tools import tools, tool_dict, invoke_tool
from USACOBench.display_utils import display_last_message
from .utils import is_finished

'''
Numbers of tokens at which we switch from normal context (8k and 4k) to
    long context models (32k and 16k), if enabled
'''
MIN_TOKENS_FOR_LONG_CONTEXT_GPT4 = 6500
MIN_TOKENS_FOR_LONG_CONTEXT_GPT3p5 = 2500
MIN_TOKENS_FOR_LONG_CONTEXT_GPT4 = 6500
MIN_TOKENS_FOR_LONG_CONTEXT_GPT3p5 = 2500

# TODO implement auto detection of batched vs. non-batched inputs
# TODO combine and abstract everything except model names
class GPT4:
    def __init__(self, **kwargs):
        self.params = kwargs
        self.enc = tiktoken.get_encoding('cl100k_base')
        
    def generate(self,
                 prompts: List[str],
                 enable_long_context=False) -> List[str]:
        '''
        Generates responses to a batch of prompts. Takes in and returns a list of (independent)
            prompts as a batch.
        '''
        max_len_prompt = np.max([len(self.enc.encode(x)) for x in prompts])
        if enable_long_context and max_len_prompt >= MIN_TOKENS_FOR_LONG_CONTEXT_GPT4:
            print('Using long context model gpt-4-32k')
            return gpts(prompts, model='gpt-4-32k', **self.params)
        else:
            return gpts(prompts, model='gpt-4', **self.params)
            
    def converse(self,
                 messages_list: List[List[Any]],
                 enable_long_context=False):
        '''
        Updates a batch of (possibly multi-turn) conversations with assistant response(s).
        '''
        # TODO implement auto long context for converse()
        if enable_long_context:
            print('Using long context model gpt-4-32k')
            responses = chatgpts_raw(messages_list, model='gpt-4-32k', **self.params)
        else:
            responses = chatgpts_raw(messages_list, model='gpt-4', **self.params)
        for messages, response in zip(messages_list, responses):
            messages.append(response)


class GPT4t:
    def __init__(self, **kwargs):
        self.params = kwargs
        self.enc = tiktoken.get_encoding('cl100k_base')
        
    def generate(self,
                 prompts: List[str],
                 enable_long_context=False) -> List[str]:
        '''
        Generates responses to a batch of prompts. Takes in and returns a list of (independent)
            prompts as a batch.
        '''
        assert enable_long_context is False
        return gpts(prompts, model='gpt-4-1106-preview', **self.params)
            
    def converse(self,
                 messages_list: List[List[Any]],
                 enable_long_context=False):
        '''
        Updates a batch of (possibly multi-turn) conversations with assistant response(s).
        '''
        assert enable_long_context is False
        responses = chatgpts_raw(messages_list, model='gpt-4-1106-preview', **self.params)
        for messages, response in zip(messages_list, responses):
            messages.append(response)

class GPT3p5:
    def __init__(self, **kwargs):
        self.params = kwargs
        self.enc = tiktoken.get_encoding('cl100k_base')
        
    def generate(self,
                 prompts: List[str],
                 enable_long_context=False) -> List[str]:
        '''
        Generates responses to a batch of prompts. Takes in and returns a list of (independent)
            prompts as a batch.
        '''
        max_len_prompt = np.max([len(self.enc.encode(x)) for x in prompts])
        if enable_long_context and max_len_prompt >= MIN_TOKENS_FOR_LONG_CONTEXT_GPT3p5:
            print('Using long context model gpt-3.5-turbo-16k')
            return gpts(prompts, model='gpt-3.5-turbo-16k', **self.params)
        else:
            return gpts(prompts, model='gpt-3.5-turbo', **self.params)
            
    def converse(self,
                 messages_list: List[List[Dict[str, Any]]],
                 enable_long_context=False):
        '''
        Updates a batch of (possibly multi-turn) conversations with assistant response(s).
        '''
        # TODO implement auto long context for converse()
        if enable_long_context:
            print('Using long context model gpt-3.5-turbo-16k')
            responses = chatgpts_raw(messages_list, model='gpt-3.5-turbo-16k', **self.params)
        else:
            responses = chatgpts_raw(messages_list, model='gpt-3.5-turbo', **self.params)
        for messages, response in zip(messages_list, responses):
            messages.append(response)

class ToolGPT:
    def __init__(self, tools=tools, tool_dict=tool_dict, **kwargs):
        if 'model' not in kwargs:
            kwargs['model'] = 'gpt-3.5-turbo' # default model
        self.params = kwargs
        self.enc = tiktoken.get_encoding('cl100k_base')
        self.tools = tools
        self.tool_dict = tool_dict
        
    def generate(self,
                 prompts: List[str],
                 enable_long_context=False,
                 max_steps=3,
                 return_messages=False,
                 verbose=False) -> List[str]:
        '''
        Generates responses to a batch of prompts. Takes in and returns a list of (independent)
            prompts as a batch.
        max_steps: max number of steps allowed
        '''
        messages_list = [[{"role": "user", "content": prompt}] for prompt in prompts]
        self.converse(messages_list,
                      enable_long_context=enable_long_context,
                      max_steps=max_steps,
                      verbose=verbose)
        if return_messages:
            return [messages[-1]['content'] for messages in messages_list], messages_list
        else:
            return [messages[-1]['content'] for messages in messages_list]

    def converse(self,
                 messages_list: List[List[Dict[str, Any]]],
                 enable_long_context=False,
                 max_steps: int = 3,
                 finished = None,
                 verbose=False):
        '''
        Updates a batch of (possibly multi-turn) conversations with assistant response(s)
            and invoked tool responses. Due to tool use each conversation may have many new
            messages added.
        max_steps: max number of steps allowed, positive int
        finished: list with same length as messages_list of booleans for whether each
            conversation is finished (useful for batching, where some conversations may have
            already ended). is finished == do not generate more
        verbose: display messages as they are generated (preceded by the last starting message)
        '''
        # TODO support max context length based cutoffs — currently need to manually set
        #     sufficiently small max_steps to avoid hitting max context length
        assert max_steps >= 1
        if verbose: # display last starting message
            display_last_message(messages_list[0])
        if enable_long_context:
            raise NotImplementedError
        else:
            # up to max_steps times, as long as generated response invokes a tool,
            #     append the tool response and reprompt
            if finished is None:
                # for each conversation, whether to keep generating
                finished = [False] * len(messages_list)
            for step in range(max_steps):
                if all(finished):
                    return
                unfinished_messages_list = [messages for messages, is_finished in 
                                            zip(messages_list, finished) if not is_finished]
                if step == max_steps-1:
                    # at the end, do not give the option of invoking a tool
                    self._step(unfinished_messages_list,
                               enable_long_context=enable_long_context,
                               verbose=verbose)
                else:
                    self._step_with_tools(unfinished_messages_list,
                                          enable_long_context=enable_long_context,
                                          verbose=verbose)
                    # update finished for any messages that are not already finished
                    finished = [finished_i or is_finished(messages) for finished_i, messages in zip(finished, messages_list)]
    
    def _step_with_tools(self,
                         messages_list: List[List[Dict[str, Any]]],
                         enable_long_context=False,
                         verbose=False):
        '''
        Updates the given batch of conversations by generates a new message step for each
            conversation in the batch allowing tool use, and possibly another message
            from any invoked tool.
        verbose: display messages as they are generated (preceded by the last starting message)
        '''
        # TODO implement long context
        if enable_long_context:
            raise NotImplementedError
        else:
            responses = chatgpts_raw(messages_list,
                         functions=self.tools,
                         function_call='auto',
                         **self.params)
            # for each conversation, add the generated response and any invoked tool's response
            for messages, response in zip(messages_list, responses):
                messages.append(response)
                if response.get("function_call"):
                    messages.append(invoke_tool(response, self.tool_dict))
            if verbose:
                if 'role' in messages_list[0][-1] and messages_list[0][-1]['role'] == 'function': # if tool was invoked, print call + output; we check if role is available since if we run out of tokens it generates a role-less message
                    display_last_message(messages_list[0][:-1])
                display_last_message(messages_list[0])

    def _step(self,
              messages_list: List[List[Any]],
              enable_long_context=False,
              verbose=False):
        '''
        Generates a new message step for each conversation in the batch, with no tool use.
        verbose: display messages as they are generated (preceded by the last starting message)
        '''
        # TODO implement auto long context for converse()
        if enable_long_context:
            raise NotImplementedError
        else:
            responses = chatgpts_raw(messages_list, **self.params)
        for messages, response in zip(messages_list, responses):
            messages.append(response)
        if verbose:
            display_last_message(messages_list[0])

# for testing
class MockGPT:
    def __init__(self, responses):
        self.responses = responses
    def generate(self, prompts):
        return self.responses
