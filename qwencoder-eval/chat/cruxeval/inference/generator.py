# Copyright (c) Meta Platforms, Inc. and affiliates.

import sys
from math import ceil

import numpy as np
from vllm import SamplingParams
from torch.utils.data import DataLoader

from utils import TokenizedDataset, complete_code

import tasks


class Generator:

    def __init__(self, model, tokenizer, args):
        self.model = model
        self.tokenizer = tokenizer
        self.args = args

    def generate(self, task_name):
        if self.args.model == "Phind/Phind-CodeLlama-34B-v2" and task_name == "output_prediction":
            task = tasks.get_task(task_name, cot=self.args.cot, phind_output=True)
        else:
            task = tasks.get_task(task_name, cot=self.args.cot, phind_output=False)

        dataset = task.get_dataset()

        if self.args.limit is not None:
            dataset = dataset.select(range(self.args.limit))

        dataset_rows = range(dataset.num_rows)
        dataset = dataset.add_column("row_index", dataset_rows)

        if self.args.end is None:
            self.args.end = dataset.num_rows
        dataset = dataset.select(range(self.args.start, self.args.end))
        dataset_rows = range(dataset.num_rows)

        # shuffle the dataset
        if self.args.shuffle:
            dataset_rows = np.random.permutation(dataset_rows)
            dataset = dataset.select(dataset_rows)

        n_tasks = dataset.num_rows

        prompts = [self.args.prefix + task.get_prompt(dataset[i]) for i in range(n_tasks)]
        task_ids = [item["id"] for item in dataset]

        if not self.args.do_sample:
            print("Greedy decoding ON: setting temperature=0.0")
            self.args.temperature = 0.0
            self.args.top_p = 1.0

        sampling_params = SamplingParams(
            n=self.args.batch_size,
            temperature=self.args.temperature,
            top_p=self.args.top_p,
            top_k=self.args.top_k,
            max_tokens=self.args.max_length_generation,
            stop=task.stop_words,
        )

        generations, generations_raw = complete_code(task, self.model, sampling_params, prompts, task_ids)

        references = [task.get_reference(dataset[i]) for i in range(n_tasks)]

        if len(list(generations.values())[0]) > self.args.n_samples:
            generations = {k: v[:self.args.n_samples] for k, v in generations.items()}
            generations_raw = {k: v[:self.args.n_samples] for k, v in generations_raw.items()}
        assert all([len(gen) == self.args.n_samples for gen in generations.values()]), f"{[len(gen) for gen in generations.values()]}"

        return generations, generations_raw, references
