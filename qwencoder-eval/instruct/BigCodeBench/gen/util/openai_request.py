import signal
import time

import openai
from openai.types.chat import ChatCompletion


def make_request(
    client: openai.Client,
    message: str,
    model: str,
    max_tokens: int = 512,
    temperature: float = 1,
    n: int = 1,
    **kwargs
) -> ChatCompletion:
    system_msg = "You are a helpful assistant good at coding."
    if (
        kwargs.get("response_format", None)
        and kwargs["response_format"]["type"] == "json_object"
    ):
        system_msg = "You are a helpful assistant designed to output JSON."

    return client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": message},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
        n=n,
        **kwargs
    )


def handler(signum, frame):
    # swallow signum and frame
    raise Exception("end of time")


def make_auto_request(*args, **kwargs) -> ChatCompletion:
    ret = None
    while ret is None:
        try:
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(100)
            ret = make_request(*args, **kwargs)
            signal.alarm(0)
        except openai.RateLimitError:
            print("Rate limit exceeded. Waiting...")
            signal.alarm(0)
            time.sleep(5)
        except openai.APIConnectionError:
            print("API connection error. Waiting...")
            signal.alarm(0)
            time.sleep(5)
        except openai.APIError as e:
            print(e)
            signal.alarm(0)
        except Exception as e:
            print("Unknown error. Waiting...")
            print(e)
            signal.alarm(0)
            time.sleep(1)
    return ret
