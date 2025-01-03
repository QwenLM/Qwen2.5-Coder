import os
import argparse
os.environ["WANDB_MODE"] = "offline"
import multiprocessing as mp
import torch
import datasets
from tqdm import tqdm
import transformers
import trl
from transformers import set_seed
from utils import init_logger
import json
from datasets import disable_caching
from dataclasses import dataclass, field
from typing import Dict, Optional, Sequence
import torch.distributed as dist
import accelerate
import warnings
warnings.filterwarnings("ignore")

disable_caching()
set_seed(1234)
tqdm.pandas()

@dataclass
class TrainingArguments(trl.ScriptArguments):
    model_max_length: int = field(
        default=512,
        metadata={"help": "Maximum sequence length. Sequences will be right padded (and possibly truncated)."},
    )
    train_test_split_ratio: float = field(
        default=0.0,
        metadata={"help": "Maximum sequence length. Sequences will be right padded (and possibly truncated)."},
    )
    truncate_source: bool = field(default=False)
    


class DPOLogCallback(transformers.TrainerCallback):
    def __init__(self, logger):
        self.logger = logger
    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs is not None:
            logs["step"] = state.global_step
            self.logger.info(f"Step {state.global_step}: Rejected Rewards = {logs['rewards/rejected']}")


class MMAPDataset(datasets.Dataset):
    def __init__(self, data_path):
        prompt_input_ids_path = data_path
        chosen_path = data_path.replace(".prompt.input_ids.mmap", ".chosen.input_ids.mmap")
        rejected_path = data_path.replace(".prompt.input_ids.mmap", ".rejected.input_ids.mmap")
        input_ids_shape_path = input_ids_path + ".shape.json"
        chosen_shape_path = labels_path + ".shape.json"
        rejected_shape_path = lengths_path + ".shape.json"
        self.model_max_length = args.model_max_length
        self.truncate_source = args.truncate_source
        with open(input_ids_shape_path, 'r') as f:
            input_ids_shape_info = json.load(f)
        with open(chosen_shape_path, 'r') as f:
            chosen_shape_info = json.load(f)
        with open(rejected_shape_path, 'r') as f:
            rejected_shape_info = json.load(f)
        self.prompt_input_ids = np.memmap(
            labels_path, 
            dtype=np.int32,
            mode='r',
            shape=(labels_shape_info['n_samples'], labels_shape_info['max_len'])
        )
        self.chosen_input_ids = np.memmap(
            lengths_path, 
            dtype=np.int32,
            mode='r',
            shape=(lengths_shape_info['n_samples'], lengths_shape_info['max_len'])
        )
        self.rejected_input_ids = np.memmap(
            lengths_path, 
            dtype=np.int32,
            mode='r',
            shape=(lengths_shape_info['n_samples'], lengths_shape_info['max_len'])
        )
        self._length = self.input_ids_shape_info['n_samples']

    def __len__(self):
        return self._length

    def __iter__(self):
        for i in range(len(self)):
            yield dict(
                prompt_input_ids=self.prompt_input_ids[index],
                chosen_input_ids=self.chosen_input_ids[index],
                rejected_input_ids=self.rejected_input_ids[index]
            )
    def __getitem__(self, i) -> Dict[str, torch.Tensor]:
        return dict(
            prompt_input_ids=self.prompt_input_ids[index],
            chosen_input_ids=self.chosen_input_ids[index],
            rejected_input_ids=self.rejected_input_ids[index]
        )

def _prepare_dataset(
        self,
        dataset,
        processing_class,
        args,
        dataset_name,
    ):
    return dataset

def train():
    parser = trl.TrlParser((TrainingArguments, trl.trainer.DPOConfig, trl.trainer.ModelConfig))
    training_args, dpo_args, model_args = parser.parse_args_and_config()
    args = {**training_args.__dict__, **dpo_args.__dict__, **model_args.__dict__}
    args = argparse.Namespace(**args)
    logger = init_logger(os.path.join(args.output_dir, 'train.log'))
    logger.info(f'args: {args}')

    model = transformers.AutoModelForCausalLM.from_pretrained(
        args.model_name_or_path,
        trust_remote_code=True,
        torch_dtype=torch.bfloat16
    )

    ref_model = transformers.AutoModelForCausalLM.from_pretrained(
        args.model_name_or_path,
        trust_remote_code=True,
        torch_dtype=torch.bfloat16
    )

    tokenizer = transformers.AutoTokenizer.from_pretrained(
        args.model_name_or_path, 
        use_fast = False, 
        trust_remote_code = True, 
        model_max_length = args.model_max_length
    )
    tokenizer.add_special_tokens({"bos_token": tokenizer.eos_token})
    tokenizer.bos_token_id = tokenizer.eos_token_id
    DPOTrainer = trl.trainer.DPOTrainer
    if args.dataset_name.endswith(".jsonl"):
        train_dataset = datasets.load_dataset('json', data_files = args.dataset_name)
        if args.train_test_split_ratio > 0:
            train_test_split = train_dataset['train'].train_test_split(test_size=args.train_test_split_ratio)
            train_dataset = train_test_split['train']
            test_dataset = train_test_split['test']
        else:
            train_dataset = train_dataset['train']
            test_dataset = None
            DPOTrainer = trl.trainer.DPOTrainer      
    elif args.dataset_name.endswith(".mmap"):
        train_dataset = MMAPDataset(args.dataset_name)
        test_dataset = None
        DPOTrainer._prepare_dataset = _prepare_dataset()
    def process_sample(row):
        system_prompt = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": row["prompt"]}
        ]
        example = {
            'prompt': tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True),
            'chosen': row["chosen"],
            'rejected': row["rejected"],
        }
        return example

    train_dataset = train_dataset.map(
        process_sample,
        num_proc = args.dataset_num_proc,
        load_from_cache_file = False,
        desc="Applying chat template into training data" 
    )
    if test_dataset is not None:
        test_dataset = test_dataset.map(
            process_sample,
            num_proc = args.dataset_num_proc,
            load_from_cache_file = False,
            desc="Applying chat template into test data" 
        )

    trainer = DPOTrainer(
        model,
        ref_model = ref_model,
        processing_class = tokenizer,
        args = dpo_args,
        train_dataset = train_dataset,
        eval_dataset = test_dataset,
        callbacks=[DPOLogCallback(logger = logger)],
    )
    trainer.train()
    trainer.save_state()
    trainer.save_model(output_dir = args.output_dir)


if __name__ == "__main__":
    train()
