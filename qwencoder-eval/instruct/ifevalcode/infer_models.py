from utils import utils
import argparse
import transformers
import json
import tqdm
import os
from openai import OpenAI
def parse_args():
    parser = argparse.ArgumentParser(description='Parameters')
    parser.add_argument("--model", "-model", default="./Qwen2.5-Coder-32B-Instruct/", type=str, help="model path")
    parser.add_argument("--use_api", "-use_api", action="store_true", help="model path")
    parser.add_argument("--input_path", "-input_path", default="./IFEvalCode.jsonl", type=str, help="")
    parser.add_argument("--output_path", "-output_path", default="./eval_results/Qwen2.5-Coder-32B-Instruct/IFEvalCode.jsonl", type=str, help="")
    parser.add_argument("--model_max_len", "-model_max_len", default=8192 * 2, type=int, help="")
    parser.add_argument("--workers", "-workers", default = 1, type=int, help="")
    parser.add_argument("--chunk_size", "-chunk_size", default = 5, type=int, help="")
    parser.add_argument("--enable_thinking", "-enable_thinking", action="store_true", help="model path")
    parser.add_argument("--chat_template", "-chat_template", default="auto", type=str, choices=["auto", "codellama"], help="")
    parser.add_argument("--base_url", "-base_url", default="http://xx.xx.xx.xx:8000/v1/", type=str, help="") #
    parser.add_argument("--api_key", "-api_key", default="token-abc123", type=str, help="") #
    parser.add_argument("--tensor_parallel_size", "-tensor_parallel_size", default=1, type=int, help="")
    args = parser.parse_args()
    return args

def unpack_data(test_data):
    data = []
    zh_prompt = "\n\n注意如果你需要使用标准库，你需要自行导入。\n\n请在第一个代码块中返回所有的完整代码。"
    en_prompt = "\n\nNote that if you need to use the standard library, you need to import it yourself. \n\nPlease return all the complete code in the first code block."
    for idx, obj in enumerate(test_data):
        data.append({
            "messages": [{"role": "user", "content": obj["chinese_question"] + zh_prompt}],
            "id": idx,
            "lg": "zh"
        })
        data.append({
            "messages": [{"role": "user", "content": obj["english_question"] + en_prompt}],
            "id": idx,
            "lg": "en"
        })
    return data

def load_cached_api_objs(objs, output_path):
    def load_cached_objs(output_path):
        result_name = os.path.basename(output_path)
        root_dir = os.path.dirname(output_path)
        file_names = [f for f in os.listdir(root_dir) if f.startswith(f"{result_name}")]
        cached_objs = {}
        for file_name in file_names:
            objs = utils.read_jsonl_file(f"{root_dir}/{file_name}")
            for obj in objs:
                if obj.get("id"):
                    cached_objs[obj["id"]] = obj
        print(f"Successfully loading {len(cached_objs)} cached objs")
        return cached_objs
    cached_objs = load_cached_objs(output_path)
    cached_cnt = 0
    left_objs = []
    for i, obj in enumerate(tqdm.tqdm(objs)):
        obj["id"] = i
        if obj["id"] in cached_objs:
            cached_cnt += 1
            continue
        left_objs.append(obj)
    cached_objs = list(cached_objs.values())
    return left_objs, cached_objs


def main():
    args = parse_args()
    print(args)
    test_data = utils.read_jsonl_file(args.input_path, max_sentence=None)
    data = unpack_data(test_data)
    if args.use_api:
        os.makedirs(os.path.dirname(args.output_path), exist_ok = True)
        input_args = {
            "model": args.model,
            "output_path": args.output_path,
            "max_tokens": args.model_max_len,
            "base_url": args.base_url,
            "api_key": args.api_key
        }
        left_objs, cached_objs = load_cached_api_objs(data, args.output_path)
        left_objs = utils.multi_tasks_from_objs(left_objs, workers = args.workers, task = utils.chat_task, chunk_size = args.chunk_size, args = input_args)
        data = left_objs + cached_objs
        data.sort(key=lambda x: x["id"])
    else:
        import vllm
        tokenizer = transformers.AutoTokenizer.from_pretrained(args.model, trust_remote_code = True)
        if hasattr(tokenizer, "model_max_length"):
            args.model_max_len = args.model_max_len if tokenizer.model_max_length > args.model_max_len else tokenizer.model_max_length
            #args.model_max_len = tokenizer.model_max_length
            print(f"max_length: {tokenizer.model_max_length}, cur_length: {args.model_max_len}")
        print(f"Model Max Length: {args.model_max_len}")
        for obj in tqdm.tqdm(data):
            if args.chat_template == "codellama":
                codellama_template = "<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{instruction} [/INST]"
                obj["input"] = codellama_template.format_map({"system_prompt": "", "instruction": obj["messages"][-1]["content"]})
            else:
                if "qwen3" in args.model:
                    obj["input"] = tokenizer.apply_chat_template(obj["messages"], add_generation_prompt = True, tokenize = False, enable_thinking = args.enable_thinking)
                else:
                    obj["input"] = tokenizer.apply_chat_template(obj["messages"], add_generation_prompt = True, tokenize = False)
        print("*****template*******")
        print(data[0]["input"])
        print("*****template*******")
        sampling_params = vllm.SamplingParams(temperature = 0.0, top_p = 0.95, max_tokens = args.model_max_len)
        # for obj in data:
        #     obj["response"] = "debug"
        model = vllm.LLM(
            model = args.model, tensor_parallel_size = args.tensor_parallel_size, # gpu_memory_utilization=0.95,
            trust_remote_code = True, max_model_len = args.model_max_len #worker_use_ray=True, 
        )
        prompts = [obj["input"] for obj in data]
        outputs = model.generate(prompts, sampling_params)
        for obj, o in zip(data, outputs):
            obj["model"] = args.model
            obj["response"] = o.outputs[0].text
    
    for idx, obj in enumerate(data):
        if idx % 2 == 0:
            test_data[idx // 2]["chinese_response"] = obj["response"] if "response" in obj else None
        else:
            test_data[idx // 2]["english_response"] = obj["response"] if "response" in obj else None
        test_data[idx // 2]["model_name"] = os.path.basename(args.model.rstrip("/"))
    utils.write_jsonl_file(test_data, args.output_path)
 
def check_data():
    objs = utils.read_jsonl_file("./IFEvalCode.jsonl")
    for obj in objs:
        if "english_response" not in obj or "chinese_response" not in obj:
            print(obj)

if __name__ == "__main__":
    main()
