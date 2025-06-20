import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, Sequence
import argparse
import torch
import transformers
import utils
from torch.utils.data import Dataset
from transformers import Trainer
import torch.distributed as dist
import sys
import os
import numpy as np
from utils import utils
from utils import training_datasets
from peft import get_peft_model, PeftConfig
IGNORE_INDEX = -100 #default ignore_index = 100 in transformers
logging.basicConfig(level=logging.DEBUG)  
@dataclass
class ModelArguments:
    model_name_or_path: Optional[str] = field(default="facebook/opt-125m")
    use_flash_attention: bool = field(default=False, metadata={"help": "Whether to use Flash Attention."})

@dataclass
class DataArguments:
    data_path: str = field(default=None, metadata={"help": "Path to the training data."})


@dataclass
class TrainingArguments(transformers.TrainingArguments):
    cache_dir: Optional[str] = field(default=None)
    optim: str = field(default="adamw_torch")
    model_max_length: int = field(
        default=512,
        metadata={"help": "Maximum sequence length. Sequences will be right padded (and possibly truncated)."},
    )
    truncate_source: bool = field(default=False)
    use_peft: bool = field(default=False)
    peft_config_path: str = field(default=None)

def smart_tokenizer_and_embedding_resize(
    special_tokens_dict: Dict,
    tokenizer: transformers.PreTrainedTokenizer,
    model: transformers.PreTrainedModel,
):
    """Resize tokenizer and embedding.

    Note: This is the unoptimized version that may make your embedding size not be divisible by 64.
    """
    num_new_tokens = tokenizer.add_special_tokens(special_tokens_dict)
    model.resize_token_embeddings(len(tokenizer))

    if num_new_tokens > 0:
        input_embeddings = model.get_input_embeddings().weight.data
        output_embeddings = model.get_output_embeddings().weight.data

        input_embeddings_avg = input_embeddings[:-num_new_tokens].mean(dim=0, keepdim=True)
        output_embeddings_avg = output_embeddings[:-num_new_tokens].mean(dim=0, keepdim=True)

        input_embeddings[-num_new_tokens:] = input_embeddings_avg
        output_embeddings[-num_new_tokens:] = output_embeddings_avg


def _tokenize_fn(strings: Sequence[str], tokenizer: transformers.PreTrainedTokenizer) -> Dict:
    """Tokenize a list of strings."""
    tokenized_list = [
        tokenizer(
            text,
            return_tensors="pt",
            padding="longest",
            max_length=tokenizer.model_max_length,
            truncation=True,
        )
        for text in strings
    ]
    input_ids = labels = [tokenized.input_ids[0] for tokenized in tokenized_list]
    input_ids_lens = labels_lens = [
        tokenized.input_ids.ne(tokenizer.pad_token_id).sum().item() for tokenized in tokenized_list
    ]
    return dict(
        input_ids=input_ids,
        labels=labels,
        input_ids_lens=input_ids_lens,
        labels_lens=labels_lens,
    )



@dataclass
class DataCollatorForSupervisedDataset(object):
    """Collate examples for supervised fine-tuning."""

    tokenizer: transformers.PreTrainedTokenizer

    def __call__(self, instances: Sequence[Dict]) -> Dict[str, torch.Tensor]:
        input_ids, labels = tuple([instance[key] for instance in instances] for key in ("input_ids", "labels"))
        input_ids = torch.nn.utils.rnn.pad_sequence(
            input_ids, batch_first=True, padding_value=self.tokenizer.pad_token_id
        )
        labels = torch.nn.utils.rnn.pad_sequence(labels, batch_first=True, padding_value=IGNORE_INDEX)
        return dict(
            input_ids=input_ids,
            labels=labels,
            attention_mask=input_ids.ne(self.tokenizer.pad_token_id),
        )


def make_supervised_data_module(tokenizer: transformers.PreTrainedTokenizer, args) -> Dict:
    """Make dataset and collator for supervised fine-tuning."""
    if args.data_path.endswith(".npy") or args.data_path.endswith(".jsonl"):
        train_dataset = training_datasets.SupervisedDataset(tokenizer=tokenizer, data_path=args.data_path, args=args)
    elif args.data_path.endswith(".mmap"):
        train_dataset = training_datasets.MMAPSupervisedDataset(tokenizer=tokenizer, data_path=args.data_path, args=args)
    data_collator = DataCollatorForSupervisedDataset(tokenizer=tokenizer)
    return dict(train_dataset=train_dataset, eval_dataset=None, data_collator=data_collator)


def is_master():
    return dist.get_rank() == 0


class SaveModelCallback(transformers.TrainerCallback):
    def on_save(self, args, state, control, **kwargs):
        output_dir = args.output_dir
        step = state.global_step
        if is_master():
            print(f"Model saved at: {output_dir}/checkpoint-{step}/")
        return control

class LoggingCallback(transformers.TrainerCallback):
    def __init__(self):
        self.start_time = None  
        self.last_time = None   
        self.last_step = 0      
        self.total_tokens = 0   

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs is not None:
            current_time = time.time()
            world_size = args.world_size
            current_step = state.global_step
            if self.start_time is None:
                self.start_time = current_time
                self.last_time = current_time
            if args.include_num_input_tokens_seen:
                tokens_processed = (state.num_input_tokens_seen - self.total_tokens) * world_size
                self.total_tokens = state.num_input_tokens_seen
            else:
                batch_size = args.per_device_train_batch_size
                max_seq_length = args.model_max_length
                steps_elapsed = current_step - self.last_step
                tokens_processed = batch_size * max_seq_length * steps_elapsed * world_size
                self.last_step = current_step
            time_elapsed = current_time - self.last_time
            tokens_per_second = tokens_processed / time_elapsed if time_elapsed > 0 else 0
            self.last_time = current_time
            log_message = {
                "loss": logs.get("loss", None),
                "learning_rate": logs.get("learning_rate", None),
                "epoch": logs.get("epoch", None),
                "step": current_step,
                "grad_norm": logs.get("grad_norm", None),
                "world_size": world_size,
                "tokens_per_second": int(tokens_per_second)
            }
            if is_master():
                print(log_message)


def find_latest_checkpoint(output_dir):
    """Find the latest checkpoint in the output directory."""
    if not os.path.exists(output_dir):
        return None
    checkpoints = [d for d in os.listdir(output_dir) if d.startswith("checkpoint-")]
    if not checkpoints:
        return None
    latest_checkpoint = max(checkpoints, key=lambda x: int(x.split("-")[-1]))
    return os.path.join(output_dir, latest_checkpoint)


class CustomTrainer(Trainer):
    def log(self, logs: Dict[str, float]) -> None:
        """
        Log `logs` on the various objects watching training.

        Subclass and override this method to inject custom behavior.

        Args:
            logs (`Dict[str, float]`):
                The values to log.
        """
        if self.state.epoch is not None:
            logs["epoch"] = self.state.epoch
        if self.args.include_num_input_tokens_seen:
            logs["num_input_tokens_seen"] = self.state.num_input_tokens_seen

        output = {**logs, **{"step": self.state.global_step}}
        self.state.log_history.append(output)
        self.control = self.callback_handler.on_log(self.args, self.state, self.control, logs)


def train():
    parser = transformers.HfArgumentParser((ModelArguments, DataArguments, TrainingArguments))
    model_args, data_args, training_args = parser.parse_args_into_dataclasses()
    args = {**model_args.__dict__, **data_args.__dict__, **training_args.__dict__}
    args = argparse.Namespace(**args)
    #logging.info(args)
    model = transformers.AutoModelForCausalLM.from_pretrained(
        model_args.model_name_or_path,
        cache_dir=training_args.cache_dir,
        attn_implementation="flash_attention_2" if model_args.use_flash_attention else None,
        trust_remote_code = True
    )
    if training_args.use_peft:
        peft_config = PeftConfig.from_pretrained(training_args.peft_config_path)
        model.enable_input_require_grads()
        model = get_peft_model(model, peft_config)
        model.print_trainable_parameters()
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        model_args.model_name_or_path,
        pad_token = '<|endoftext|>',
        eos_token = '<|im_end|>', #<|endoftext|>
        cache_dir = None,
        model_max_length = training_args.model_max_length,
        truncation = True,
        padding_side = "right",
        trust_remote_code = True
    )
    tokenizer.add_special_tokens({"additional_special_tokens": ["<|im_end|>", "<|im_start|>"]})
    data_module = make_supervised_data_module(tokenizer=tokenizer, args=args)
    #trainer = CustomTrainer(
    trainer = Trainer(
        model=model, 
        tokenizer=tokenizer, 
        args=training_args, 
        **data_module, 
        callbacks=[LoggingCallback, SaveModelCallback]
    )
    trainer.train()
    trainer.save_state()
    trainer.save_model(output_dir=training_args.output_dir)

if __name__ == "__main__":
    train()
