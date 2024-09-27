# Copyright (c) Meta Platforms, Inc. and affiliates.

import json
from abc import ABC, abstractmethod
from warnings import warn

from datasets import load_dataset, Dataset


class Task(ABC):
    """A task represents an entire benchmark including its dataset, problems,
    answers, generation settings and evaluation methods.
    """

    # The name of the `Task` benchmark as denoted in the HuggingFace datasets Hub
    DATASET_PATH: str = None

    # The name of a subset within `DATASET_PATH`.
    DATASET_NAME: str = None

    def __init__(self, stop_words=None, requires_execution=True):
        """
        :param stop_words: list
            list of stop words if the generation uses a stopping criteria during generation
        :param requires_execution: bool
            wheter the task requires code execution during evaluation or not
        """
        self.stop_words = stop_words
        self.requires_execution = requires_execution

        # Load the dataset from local file
        with open(self.DATASET_PATH, "r") as f:
            lines = f.readlines()
        lines_json = [json.loads(i) for i in lines]
        data = {}
        columns = ["code", "input", "output", "id"]
        for k in columns:
            data[k] = []
        for l in lines_json:
            for k in columns:
                data[k].append(l[k])
        data = Dataset.from_dict(data, split="test")
        self.dataset = data
        warn("This task will use a locally downloaded dataset, not from the HF hub.")

    @abstractmethod
    def get_dataset(self):
        """Returns dataset for the task or an iterable of any object, that get_prompt can handle"""
        return []

    def fewshot_examples(self):
        """Loads and returns the few-shot examples for the task if they exist."""
        pass

    @abstractmethod
    def get_prompt(self, doc):
        """Builds the prompt for the LM to generate from.
        :param doc: dict[str: str]
            sample from the test dataset
        """
        pass

    @abstractmethod
    def get_reference(self, doc):
        """Builds the reference solution for the doc.
        :param doc: dict[str: str]
            sample from the test dataset
        """
        pass

    @abstractmethod
    def postprocess_generation(self, generation, idx):
        """Defines the postprocessing for a LM generation.
        :param generation: str
            code generation from LM
        :param idx: int
            index of doc in the dataset to which the generation belongs
        """
        pass

    @abstractmethod
    def process_results(self, generations, references):
        """Takes the list of LM generations and evaluates them against ground truth references,
        returning the metric for the generations as in {"metric_name": result}.
        :param generations: list(list(str))
            list of lists containing generations
        :param references: list(str)
            list of str containing refrences
        :return: dict[str: float]
        """
        pass
