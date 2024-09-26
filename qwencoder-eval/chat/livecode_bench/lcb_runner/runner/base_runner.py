import os
import json
from abc import ABC, abstractmethod

from tqdm import tqdm

from lcb_runner.lm_styles import LanguageModel
from lcb_runner.utils.path_utils import get_cache_path
from lcb_runner.utils.multiprocess import run_tasks_in_parallel


class BaseRunner(ABC):
    def __init__(self, args, model: LanguageModel):
        self.args = args
        self.model = model

        if self.args.use_cache:
            self.cache_path = get_cache_path(model, args)
            if os.path.exists(self.cache_path):
                with open(self.cache_path) as f:
                    self.cache: dict = json.load(f)
            else:
                self.cache = {}
        else:
            self.cache_path = None
            self.cache = None

    def save_cache(self):
        if self.args.use_cache:
            with open(self.cache_path, "w") as f:
                json.dump(self.cache, f, indent=4)

    @abstractmethod
    def _run_single(self, prompt: str) -> str:
        pass

    def run_single(self, prompt: str) -> str:
        if self.args.use_cache:
            try:
                with open(self.cache_path, "r") as f:
                    cache = json.load(f)
            except FileNotFoundError:
                pass

            cached_values = cache["data"]

            if prompt in cache:
                cache_result = cache[prompt]
                if len(cache_result) == self.args.n:
                    return cache_result

        result = self._run_single(prompt)

        if self.args.use_cache:
            cache[prompt] = result

    def run_batch(self, prompts: list[str]) -> list[str]:
        if self.args.multiprocess > 1:
            return run_tasks_in_parallel(
                self.run_single,
                prompts,
                self.args.multiprocess,
                self.args.timeout,
                True,
            )
        return [self.run_single(prompt) for prompt in tqdm(prompts)]

    def run_main(self, benchmark: list, format_prompt: callable) -> list:
        prompts = [
            format_prompt(problem, self.model.model_style) for problem in benchmark
        ]
        outputs = self.run_batch(prompts)
        self.save_cache()
        return outputs
