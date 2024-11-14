import inspect
from pprint import pprint

from . import (
    spider_dev,
    bird_dev,
    spider_dev_chat,
    spider_dev_chat_cot,
    bird_dev_chat,
    bird_dev_chat_cot,
)

TASK_REGISTRY = {
    "spider-dev": spider_dev.SpiderDev,
    "bird-dev": bird_dev.BirdDev,
    "bird-dev-nokg": bird_dev.BirdDevNoKG,
    # ----- chat model -----
    "spider-dev-chat": spider_dev_chat.SpiderDevChat,
    "spider-dev-chat-cot": spider_dev_chat_cot.SpiderDevChat,
    "bird-dev-chat": bird_dev_chat.BirdDevChat,
    "bird-dev-chat-cot": bird_dev_chat_cot.BirdDevChat,
}

ALL_TASKS = sorted(list(TASK_REGISTRY))


def get_task(task_name, args=None):
    try:
        kwargs = {}
        if "prompt" in inspect.signature(TASK_REGISTRY[task_name]).parameters:
            kwargs["prompt"] = args.prompt
        if "load_data_path" in inspect.signature(TASK_REGISTRY[task_name]).parameters:
            kwargs["load_data_path"] = args.load_data_path
        return TASK_REGISTRY[task_name](**kwargs)
    except KeyError:
        print("Available tasks:")
        pprint(TASK_REGISTRY)
        raise KeyError(f"Missing task {task_name}")
