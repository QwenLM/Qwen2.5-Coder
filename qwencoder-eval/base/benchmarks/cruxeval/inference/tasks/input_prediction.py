# Copyright (c) Meta Platforms, Inc. and affiliates.

from pathlib import Path

from .base import Task

from prompts import (
    make_direct_input_prompt,
    make_cot_input_prompt,
)


class InputPrediction(Task):
    """A task represents an entire benchmark including its dataset, problems,
    answers, generation settings and evaluation methods.
    """

    DATASET_PATH = str(Path(__file__).resolve().parent.parent.parent / "data/cruxeval.jsonl")
    DATASET_NAME = None

    def __init__(self, cot=False):
        self.cot = cot
        super().__init__(
            stop_words=["[/ANSWER]"],
            requires_execution=False,
        )

    def get_dataset(self):
        """Returns dataset for the task or an iterable of any object, that get_prompt can handle"""
        return self.dataset

    def get_prompt(self, doc):
        if self.cot:
            return make_cot_input_prompt((doc["code"], doc["output"]))
        else:
            return make_direct_input_prompt((doc["code"], doc["output"]))

    def get_reference(self, doc):
        return (doc["code"], doc["input"], doc["output"])

    def postprocess_generation(self, generation, idx):
        prompt = self.get_prompt(self.get_dataset()[idx])
        assert generation.startswith(prompt)

        generation = generation[len(prompt) :]
        if self.cot:
            if "[ANSWER]" in generation:
                generation = generation.split("[ANSWER]")[1].strip()
        if "==" in generation:
            generation = generation.split("==")[0].strip()
        if "assert f" in generation:
            generation = "f" + generation.split("assert f")[1].strip()
        return generation.strip()

    def process_results(self, generations, references):
        return {}
