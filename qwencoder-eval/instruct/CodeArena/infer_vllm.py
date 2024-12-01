from utils import utils
import argparse
import transformers
import json
import tqdm
import vllm
import openai
from openai import OpenAI
def parse_args():
    parser = argparse.ArgumentParser(description='Parameters')
    parser.add_argument("--model", "-model", default="", type=str, help="model path")
    parser.add_argument("--input_path", "-input_path", default="./CodeArena_v1.jsonl", type=str, help="")
    parser.add_argument("--output_path", "-output_path", default="./results/yi-lightning/results.jsonl", type=str, help="")
    parser.add_argument("--model_max_len", "-model_max_len", default=8192 * 2, type=int, help="")
    parser.add_argument("--chat_template", "-chat_template", default="auto", type=str, choices=["auto", "codellama"], help="")
    parser.add_argument("--tensor_parallel_size", "-tensor_parallel_size", default=1, type=int, help="")
    args = parser.parse_args()
    return args

def api_query(messages, model_name):
    if model_name == "yi-lightning":
        API_BASE = "https://api.lingyiwanwu.com/v1"
        API_KEY = ""
        client = OpenAI(
            api_key=API_KEY,
            base_url=API_BASE
        )
        completion = client.chat.completions.create(
            model="yi-lightning",
            messages=messages
        )
        return completion.choices[0].message.content

def main():
    args = parse_args()
    print(args)
    test_data = utils.read_jsonl_file(args.input_path, max_sentence=None)
    objs = []
    api_models = ["yi-lightning"]
    if args.model in api_models:
        generated_objs = []
        for obj in tqdm.tqdm(test_data):
            obj["model"] = args.model
            obj["response"] = api_query(obj["messages"], args.model)
            generated_objs.append(obj)
    else:
        tokenizer = transformers.AutoTokenizer.from_pretrained(args.model, trust_remote_code = True)
        if hasattr(tokenizer, "model_max_length"):
            args.model_max_len = args.model_max_len if tokenizer.model_max_length > args.model_max_len else tokenizer.model_max_length
            print(f"max_length: {tokenizer.model_max_length}, cur_length: {args.model_max_len}")
        print(f"Model Max Length: {args.model_max_len}")
        for obj in tqdm.tqdm(test_data):
            if args.chat_template == "codellama":
                codellama_template = "<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{instruction} [/INST]"
                obj["input"] = codellama_template.format_map({"system_prompt": "", "instruction": obj["messages"][-1]["content"]})
            else:
                obj["input"] = tokenizer.apply_chat_template(obj["messages"], add_generation_prompt=True, tokenize=False)
            objs.append(obj)
        sampling_params = vllm.SamplingParams(temperature = 0.0, top_p = 0.95, max_tokens = args.model_max_len)
        model = vllm.LLM(
            model = args.model, tensor_parallel_size = args.tensor_parallel_size, # gpu_memory_utilization=0.95,
            worker_use_ray=True, trust_remote_code = True, max_model_len = args.model_max_len
        )
        generated_objs = []
        prompts = [obj["input"] for obj in objs]
        outputs = model.generate(prompts, sampling_params)
        for obj, o in zip(objs, outputs):
            obj["model"] = args.model
            obj["response"] = o.outputs[0].text
            generated_objs.append(obj)
    utils.write_jsonl_file(generated_objs, args.output_path)
 
if __name__ == "__main__":
    main()