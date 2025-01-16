from transformers import AutoTokenizer
import argparse
from peft import AutoPeftModelForCausalLM, PeftConfig

def merge_model(args):
    model_name_or_path = args.input_model_path
    input_adapter_path = args.input_adapter_path
    output_dir = args.output_path

    peft_config = PeftConfig.from_pretrained(input_adapter_path)
    peft_config.base_model_name_or_path = model_name_or_path
    peft_model = AutoPeftModelForCausalLM.from_pretrained(
        input_adapter_path,
        config=peft_config,
    )
    merged_model = peft_model.merge_and_unload(progressbar=True)
    merged_model.save_pretrained(output_dir)

    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
    tokenizer.save_pretrained(output_dir)

def parse_args():
    parser = argparse.ArgumentParser(description='Argument Parser Example')
    parser.add_argument('--input_model_path', '-input_model_path', type=str, default="/cpfs01/data/shared/Group-m6/chuwei.zw/models/Qwen/Qwen2.5-Coder-1.5B", help='Path to model')
    parser.add_argument('--input_adapter_path', '-input_adapter_path', type=str, default="/cpfs01/data/shared/Group-m6/chuwei.zw/models/checkpoints/1.5B/sft-test-version", help='Path to adapter folder')
    parser.add_argument('--output_path', '-output_path', type=str, default="/cpfs01/data/shared/Group-m6/chuwei.zw/models/checkpoints/1.5B/sft-test-version-merge", help='Path to output folder')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    print(args)
    merge_model(args)