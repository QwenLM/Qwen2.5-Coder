import jsonlines
import tqdm
import numpy as np
def convert_file():
    def read_jsonl_file(file_name, max_sentence=None):
        data = []
        with jsonlines.open(file_name, "r") as r:
            for i, obj in tqdm.tqdm(enumerate(r)):
                if max_sentence is not None and i >= max_sentence:
                    return data
                data.append(obj)
        return data
    
    def write_jsonl_file(file_name, data):
        with jsonlines.open(file_name, "w") as w:
            for obj in data:
                w.write(obj)
        print(f"Successfully saving to {file_name}")


    def get_humaneval_prompt(doc, language):
        language = language.lower()
        question = doc["prompt"].strip()
        return """
Please continue to complete the function and return all completed code in a codeblock. Here is the given code to do completion:
```{}
{}
```
""".strip().format(
        language.lower(), question.strip()
    )

    def convert(sample, program_language):
        prompt = get_humaneval_prompt(sample, program_language)
        tests = sample["tests"] if "tests" in sample else sample["test"]
        data = {
            "base_prompt": sample["prompt"],
            "name": sample["name"] if "name" in sample else None,
            "prompt": prompt,
            "test": tests,
            "tags": f"coding,en,{program_language},core",
            "program_language": program_language,
            "task": f"MultiPL_E/{program_language}",
            "source": f"MultiPL_E",
            "eval_args": {
                "greedy": True,
                "seed": 1234,
                "out_seq_length": 1560,		                              
                "repetition_penalty": 1.0,
                "temperature": 0.01,
                #"presence_penalty": 2.0,
                #"system_str": "你是一个专业的数学家，擅长解答数学问题。",   // 覆盖默认system字符串，用于一些特殊任务，如数学等。
                "top_k": -1,
                "top_p": 0.95,
            }
        }
        return data
    
    root_dir = "./MultiPL-E/"
    all_data = []
    for lg in ["python", "sh", "java", "js", "cpp", "php", "cs", "ts"]:
        objs = read_jsonl_file(f"./chat/data/humaneval/humaneval-{lg}.jsonl")
        new_data = []
        for obj in objs:
            new_obj = convert(obj, lg)
            new_data.append(new_obj)
        all_data += new_data
        write_jsonl_file(f"{root_dir}/humaneval_{lg}.jsonl", new_data)
    write_jsonl_file(f"{root_dir}/MultiPL-E.jsonl", all_data)
    all_data = np.random.choice(all_data, 10)
    write_jsonl_file(f"{root_dir}/MultiPL-E.jsonl.sampled", all_data)


if __name__ == "__main__":
    convert_file()