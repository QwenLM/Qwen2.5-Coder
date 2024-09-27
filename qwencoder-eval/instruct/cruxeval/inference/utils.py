# Copyright (c) Meta Platforms, Inc. and affiliates.

from collections import defaultdict

from torch.utils.data import IterableDataset


class TokenizedDataset(IterableDataset):
    """Tokenize and preprocess the dataset
    Multiple copies of the same prompt are sent sequentially. See compute_code for more details.
    The prompt can either be:
    - one prompt: normal code completion
    - two prompts: for infilling mode (prefix, suffix) or instructin-tuning mode (instruction, context)
    """

    def __init__(
        self,
        task,
        dataset,
        tokenizer,
        max_length,
        n_tasks=None,
        n_copies=1,
        prefix="",
    ):
        self.task = task
        self.dataset = dataset
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.n_tasks = n_tasks
        self.n_copies = n_copies
        self.prefix = prefix

    def __iter__(self):
        prompts = []
        row_idxs = []
        for sample in range(self.n_tasks):
            dataset_sample = self.dataset[sample]
            prompt_contents = self.task.get_prompt(dataset_sample)
            assert isinstance(prompt_contents, str)
            prompt = self.prefix + prompt_contents
            prompts.append(prompt)
            row_idxs.append(dataset_sample["row_index"])

        return_token_type_ids = None  # default

        outputs = self.tokenizer(
            prompts,
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=self.max_length,
            return_token_type_ids=return_token_type_ids,
        )

        for sample in range(self.n_tasks):
            for _ in range(self.n_copies):
                yield {
                    "row_index": row_idxs[sample],
                    "prompt": prompts[sample],
                    "ids": outputs.input_ids[sample],
                    "input_len": outputs.attention_mask[sample].sum(),
                }


def complete_code(
    task,
    model,
    sampling_params,
    prompts,
    task_ids,
    postprocess=True,
):

    outputs = model.generate(
        prompts=prompts,
        sampling_params=sampling_params,
        use_tqdm=True,
    )

    generated_texts = [output.outputs[0].text for output in outputs]
    combined_texts = [prompt + generated_text for prompt, generated_text in zip(prompts, generated_texts)]

    code_gens, code_gens_raw = defaultdict(list), defaultdict(list)
    for task_id, text in zip(task_ids, combined_texts):
        if postprocess:
            text_processed = task.postprocess_generation(text, int(task_id.split("_")[-1]))
        code_gens[task_id].append(text_processed)
        code_gens_raw[task_id].append(text)

    return code_gens, code_gens_raw
