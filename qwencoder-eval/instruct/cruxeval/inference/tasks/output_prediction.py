# Copyright (c) Meta Platforms, Inc. and affiliates.

from pathlib import Path

from .base import Task

from prompts import (
    make_direct_output_prompt,
    make_direct_output_prompt_phind,
    make_cot_output_prompt,
)


class OutputPrediction(Task):
    """A task represents an entire benchmark including its dataset, problems,
    answers, generation settings and evaluation methods.
    """

    DATASET_PATH = str(Path(__file__).resolve().parent.parent.parent / "data/cruxeval.jsonl")
    DATASET_NAME = None

    def __init__(self, cot=False, phind_output=False):
        self.cot = cot
        self.phind_output = phind_output

        if self.phind_output:
            stop_words = ["# done"]
        else:
            stop_words = ["[/ANSWER]"]

        super().__init__(
            stop_words=stop_words,
            requires_execution=False,
        )

    def get_dataset(self):
        """Returns dataset for the task or an iterable of any object, that get_prompt can handle"""
        return self.dataset

    def get_prompt(self, doc):
        if self.phind_output:
            return make_direct_output_prompt_phind((doc["code"], doc["input"]))
        elif self.cot:
            return make_cot_output_prompt((doc["code"], doc["input"]))
        else:
            return make_direct_output_prompt((doc["code"], doc["input"]))

    def get_reference(self, doc):
        return (doc["code"], doc["input"], doc["output"])

    def postprocess_generation(self, generation, idx):
        prompt = self.get_prompt(self.get_dataset()[idx])
        assert generation.startswith(prompt)
        generation = generation[len(prompt):]

        if self.cot:
            if "[ANSWER]" in generation:
                generation = generation.split("[ANSWER]")[1].strip()
        if "==" in generation:
            generation = generation.split("==")[1].strip()
        return generation.strip()

    def process_results(self, generations, references):
        return {}
