import os 
import re 
import json 
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()


def extract_ccpp_code(text, item, ):
    code_block = re.search(rf"```(?:[Cc](?:pp|\+\+|PP)?)?(.*?)\n```", text, flags=re.DOTALL)
    if code_block is None:
        code_block_pattern = re.compile(rf"(\n.*?\s+{item['entry_point']}.*}})", re.DOTALL)
        code_block = code_block_pattern.search(text)
    if code_block is None:
        code = text
    else:
        code = code_block.group(1)
    
    includes_pattern = re.compile(r"(#include\s+<[^>]+>)", re.MULTILINE)
    includes = includes_pattern.findall(code)
    code = re.sub(r"(#include\s+<[^>]+>)", "\n", code, flags=re.DOTALL).strip()
    code = re.sub(r'int\s+main\s*\(.*?\)\s*\{.*?return 0;.*?\}', '', code, flags=re.DOTALL).strip()

    code = re.sub(r'void\s+check\w*\s*\(.*?\)\s*\{.*\}', '', code, flags=re.DOTALL).strip()

    
    prompt = item['prompt'].split('\n')
    prompt = '\n'.join(prompt[:-1])
    if item['signature'] in prompt:
        prompt = prompt.replace(item['signature'], '')
    full_code = '\n'.join(includes) + '\n' + prompt +'\n'+ code+'\n' + item['test']

    return full_code




if __name__ == '__main__':
    items = [json.loads(x) for x in open('eval/generations/gpt4/completions_C_humanevalsynthesize.jsonl').readlines() if x]

    for item in [items[0]]:
        prt = extract_ccpp_code(item['raw_generation'][0], item)
        print('"'* 60)
        print(prt)
        # break