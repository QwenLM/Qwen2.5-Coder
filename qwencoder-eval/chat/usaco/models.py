import os
import openai
import asyncio
from openai import AsyncOpenAI
from typing import List, Dict, Union
from tqdm.asyncio import tqdm_asyncio
import anthropic
import backoff

from dotenv import load_dotenv

load_dotenv()

completion_tokens = {"gpt-4": 0, "gpt-4-1106-preview": 0, "gpt-3.5-turbo": 0, "gpt-3.5-turbo-16k": 0}
prompt_tokens = {"gpt-4": 0, "gpt-4-1106-preview": 0, "gpt-3.5-turbo": 0, "gpt-3.5-turbo-16k": 0}


async def generate_from_openai_chat_completion(
    messages_list: List[Dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
    stop: Union[str, List[str]],
    requests_per_minute: int = 300,
    verbose=False,
    **kwargs,
) -> List[str]:
    client = AsyncOpenAI(
        base_url=os.getenv("OPENAI_API_BASE", None),
        api_key=os.getenv("OPENAI_API_KEY", None),
    )
    async_responses = []
    for message in messages_list:
        task = asyncio.create_task(generate_answer(message, client, model, temperature))
        async_responses.append(task)
    responses = await tqdm_asyncio.gather(*async_responses, disable=not verbose)
    return responses


@backoff.on_exception(backoff.expo, openai.RateLimitError)
async def generate_answer(prompt, client: AsyncOpenAI, model, temperature):
    """
    Send a prompt to OpenAI API and get the answer.
    :param prompt: the prompt to send.
    :return: the answer.
    """
    response = await client.chat.completions.create(
        model=model,
        messages=prompt,
        temperature=temperature,
    )
    return response


async def generate_from_anthropic_chat_completion(
    messages_list: List[str],
    model: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
    stop: Union[str, List[str]],
    requests_per_minute: int = 300,
    verbose=False,
    **kwargs,
) -> List[str]:
    client = anthropic.AsyncAnthropic()
    async_responses = []
    for message in messages_list:
        task = asyncio.create_task(generate_answer_anthropic(message, client, model, max_tokens))
        async_responses.append(task)
    responses = await tqdm_asyncio.gather(*async_responses, disable=not verbose)
    return responses


@backoff.on_exception(backoff.expo, anthropic.RateLimitError)
async def generate_answer_anthropic(message, client, model, max_tokens):
    """
    Send a prompt to OpenAI API and get the answer.
    :param prompt: the prompt to send.
    :return: the answer.
    """
    response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=message,
    )
    return response


def gpt(prompt, model="gpt-4", temperature=0.7, max_tokens=2000, n=1, stop=None, **kwargs) -> list:
    return gpts([prompt] * n, model=model, temperature=temperature, max_tokens=max_tokens, stop=stop, **kwargs)[0]


def gpts(prompts, model="gpt-4", temperature=0.7, max_tokens=2000, stop=None, system_prompt: str = None, **kwargs) -> list:
    '''
    system_prompt: string added as a special system message at the beginning of the conversation
    '''
    if system_prompt is not None:
        messages_list = [[{'role': 'system', 'content': system_prompt}, {"role": "user", "content": prompt}] for prompt in prompts]
    else:
        messages_list = [[{"role": "user", "content": prompt}] for prompt in prompts]
    return chatgpts(messages_list, model=model, temperature=temperature, max_tokens=max_tokens, stop=stop, **kwargs)


def chatgpt(messages, model="gpt-4", temperature=0.7, max_tokens=2000, n=1, stop=None, **kwargs) -> list:
    return chatgpts([messages] * n, model=model, temperature=temperature, max_tokens=max_tokens, stop=stop, **kwargs)[0]


def chatgpt_raw(messages, model="gpt-4", temperature=0.7, max_tokens=2000, n=1, stop=None, **kwargs) -> list:
    return chatgpts_raw([messages] * n, model=model, temperature=temperature, max_tokens=max_tokens, stop=stop, **kwargs)[0]


def chatgpts(messages_list, model="gpt-4", temperature=0.7, max_tokens=2000, stop=None, max_messages=400, **kwargs) -> list:
    texts = []
    for i in range(0, len(messages_list), max_messages):
        responses = asyncio.run(generate_from_openai_chat_completion(model=model, messages_list=messages_list[i:i + max_messages], temperature=temperature, max_tokens=max_tokens, top_p=1, stop=stop, **kwargs))
        texts.extend([x.choices[0].message.content for x in responses])
        # global completion_tokens, prompt_tokens
        # completion_tokens[model] += sum(x["usage"]["completion_tokens"] for x in responses if "usage" in x and "completion_tokens" in x["usage"])
        # prompt_tokens[model] += sum(x["usage"]["prompt_tokens"] for x in responses if "usage" in x and "prompt_tokens" in x["usage"])
    return texts


def chatgpts_raw(messages_list, model="gpt-4", temperature=0.7, max_tokens=2000, stop=None, max_messages=400, **kwargs) -> list:
    '''
    Returns raw response messages, not just the text content
    '''
    responses_all = []
    for i in range(0, len(messages_list), max_messages):
        responses = asyncio.run(generate_from_openai_chat_completion(model=model, messages_list=messages_list[i:i + max_messages], temperature=temperature, max_tokens=max_tokens, top_p=1, stop=stop, **kwargs))
        responses_all.extend([x["choices"][0]["message"] for x in responses])
        # global completion_tokens, prompt_tokens
        # completion_tokens[model] += sum(x["usage"]["completion_tokens"] for x in responses if "usage" in x and "completion_tokens" in x["usage"])
        # prompt_tokens[model] += sum(x["usage"]["prompt_tokens"] for x in responses if "usage" in x and "prompt_tokens" in x["usage"])
    return responses_all


def claude(prompts, model="claude-3-sonnet-20240229", temperature=0.7, max_tokens=3000, stop=None, max_messages=400, system_prompt=None, **kwargs) -> list:
    texts = []
    if system_prompt is not None:
        messages_list = [[{'role': 'system', 'content': system_prompt}, {"role": "user", "content": prompt}] for prompt in prompts]
    else:
        messages_list = [[{"role": "user", "content": prompt}] for prompt in prompts]
    for i in range(0, len(prompts), max_messages):
        responses = asyncio.run(generate_from_anthropic_chat_completion(model=model, messages_list=messages_list, temperature=temperature, max_tokens=max_tokens, top_p=1, stop=stop, **kwargs))
        texts.extend([x.content[0].text for x in responses])
        # global completion_tokens, prompt_tokens
        # completion_tokens[model] += sum(x["usage"]["completion_tokens"] for x in responses if "usage" in x and "completion_tokens" in x["usage"])
        # prompt_tokens[model] += sum(x["usage"]["prompt_tokens"] for x in responses if "usage" in x and "prompt_tokens" in x["usage"])
    return texts


def gpt_usage():
    global completion_tokens, prompt_tokens
    cost = completion_tokens["gpt-4"] / 1000 * 0.06 + prompt_tokens["gpt-4"] / 1000 * 0.03
    cost += completion_tokens["gpt-4-1106-preview"] / 1000 * 0.03 + prompt_tokens["gpt-4-1106-preview"] / 1000 * 0.01
    cost += completion_tokens["gpt-3.5-turbo"] / 1000 * 0.002 + prompt_tokens["gpt-3.5-turbo"] / 1000 * 0.0015
    cost += completion_tokens["gpt-3.5-turbo-16k"] / 1000 * 0.004 + prompt_tokens["gpt-3.5-turbo-16k"] / 1000 * 0.003
    return {"completion_tokens": completion_tokens, "prompt_tokens": prompt_tokens, "cost": cost}
