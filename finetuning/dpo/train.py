import os
os.environ["WANDB_MODE"] = "offline"
import multiprocessing
import torch
from datasets import load_dataset
from tqdm import tqdm
import transformers
import trl
from trl.trainer import DPOConfig,DPOTrainer,ModelConfig
from trl.commands.cli_utils import DPOScriptArguments, TrlParser
from transformers import set_seed
from utils import init_logger
import json
from datasets import disable_caching

disable_caching()
set_seed(1234)
tqdm.pandas()


def train():
    parser = TrlParser((DPOScriptArguments, DPOConfig, ModelConfig))
    args, training_args, model_config = parser.parse_args_and_config()

    logger = init_logger(
        os.path.join(training_args.output_dir, 'train.log'),
        training_args.local_rank
    )
    logger.info(f'model args: {model_config}')
    logger.info(f'args: {args}')
    logger.info(f'training args: {training_args}')

    model = transformers.AutoModelForCausalLM.from_pretrained(
            model_config.model_name_or_path,
            trust_remote_code=True,
            torch_dtype=torch.bfloat16
        )

    model_ref = transformers.AutoModelForCausalLM.from_pretrained(
            model_config.model_name_or_path,
            trust_remote_code=True,
            torch_dtype=torch.bfloat16
        )

    tokenizer = transformers.AutoTokenizer.from_pretrained(model_config.model_name_or_path, use_fast=False, trust_remote_code=True, model_max_length=training_args.max_length)
    tokenizer.add_special_tokens({"bos_token": tokenizer.eos_token})
    tokenizer.bos_token_id = tokenizer.eos_token_id

    train_dataset = load_dataset('json', data_files=args.dataset_name)
    train_test_split = train_dataset['train'].train_test_split(test_size=0.1)
    train_dataset = train_test_split['train']
    test_dataset = train_test_split['test']

    def process(row):
        messages = [
                    {"role": "system", "content": "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."},
                    {"role": "user", "content": row["prompt"]}
                ]
        example = {
                    'prompt': tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True),
                    'chosen': row["chosen"],
                    'rejected': row["rejected"],
                }
        return example

    train_dataset = train_dataset.map(
        process,
        num_proc=multiprocessing.cpu_count(),
        load_from_cache_file=False,
    )

    test_dataset = test_dataset.map(
        process,
        num_proc=multiprocessing.cpu_count(),
        load_from_cache_file=False,
    )

    trainer = DPOTrainer(
        model,
        model_ref,
        tokenizer=tokenizer,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
    )
    trainer.train()
    trainer.save_state()
    trainer.save_model(output_dir=training_args.output_dir)


if __name__ == "__main__":
    train()
