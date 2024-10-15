import re
import json

def extract_erlang_code(text, item) -> str:
    entry_point = item["entry_point"]
    prompt = item["prompt"]
    code = text
    code_block = re.search(
        rf"```(?:[Ee]rlang)?.*?(-module.*{entry_point}.*?->.*?)```", text, flags=re.DOTALL)
    
    if code_block is None:
        code_block = re.search(
            rf"```(?:[Ee]rlang)?.*?({entry_point}.*?->.*?)```", text, flags=re.DOTALL) 

    if code_block is None:
        # code_block = re.search(rf"(-module.*{entry_point}.*?->.*?end)", text, flags=re.DOTALL)
        code_block = re.search(rf"({entry_point}.*?\-\>.*?)", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(
            rf"```(?:[Ee]rlang)?(.*?)```", text, flags=re.DOTALL)
    if code_block is None:
        code = text
    else:
        code = code_block.group(1)

    if (code.find("test()") != -1):
        code = code[:code.find("test()")]
        
    code_block_post = re.search(rf"(-module.*export.*\n)?({entry_point}.*?->.*)", code, flags=re.DOTALL)
    if code_block_post is None:
        return code + item['test']
    else:
        new_code = prompt.split(
            "\n")[0]+'\n'+prompt.split("\n")[1]+"\n\n"+code_block_post.group(2)
        return new_code + item['test']


if __name__ == '__main__':
    items = [json.loads(x) for x in open(
        'completions_Erlang_humanevalsynthesize.jsonl').readlines() if x]

    for item in items:
        extract_erlang_code(item['raw_generation'][0], item)
