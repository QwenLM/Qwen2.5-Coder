from transformers import AutoTokenizer
import argparse
from peft import AutoPeftModelForCausalLM, PeftConfig
import os

def merge_all_checkpoint_with_adapter(base_model_path, train_adapters_path, output_path):
    for root, dirs, files in os.walk(train_adapters_path):
        for dir in dirs:
            if dir.startswith("checkpoint-"):
                adapter_dir = os.path.join(root, dir)
                merged_ckpt_dir = os.path.join(output_path, dir)
                merge_adapter(base_model_path, adapter_dir, merged_ckpt_dir)

def merge_adapter(base_model_path, adapter_dir, output_path):
    peft_config = PeftConfig.from_pretrained(adapter_dir)
    peft_config.base_model_name_or_path = base_model_path
    peft_model = AutoPeftModelForCausalLM.from_pretrained(
        adapter_dir,
        config=peft_config,
    )
    merged_model = peft_model.merge_and_unload(progressbar=True)
    merged_model.save_pretrained(output_path)
    tokenizer = AutoTokenizer.from_pretrained(base_model_path)
    tokenizer.save_pretrained(output_path)

def parse_args():
    parser = argparse.ArgumentParser(description='Argument Parser Example')
    parser.add_argument('--base_model_path', '-base_model_path', type=str, default="/cpfs01/data/shared/Group-m6/chuwei.zw/models/Qwen/Qwen2.5-Coder-1.5B", help='Path to model')
    parser.add_argument('--train_adapters_path', '-train_adapters_path', type=str, default="/cpfs01/data/shared/Group-m6/chuwei.zw/models/checkpoints/1.5B/sft-test-version", help='Path to adapter folder')
    parser.add_argument('--output_path', '-output_path', type=str, default="/cpfs01/data/shared/Group-m6/chuwei.zw/models/checkpoints/1.5B/sft-test-version-merge", help='Path to output folder')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    print(args)
    # 最后一个再保存一下
    merge_all_checkpoint_with_adapter(args.base_model_path, args.train_adapters_path, args.output_path)
    # all
    merge_adapter(args.base_model_path, args.train_adapters_path, args.output_path)
    

