import os 
import re 
import json 
import textwrap
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()


def extract_rust_code_block(text: str, entry_point) -> str:
    code_block_pattern = re.compile(rf"```(?:[Rr]ust)?(.*?fn\s+{entry_point}.*?)```", re.DOTALL)
    code_block = code_block_pattern.search(text)

    if code_block is None:
        code_block_pattern = re.compile(rf"```(?:[Rr]ust)?(.*?fn\s+{entry_point}.*?)$", re.DOTALL)
        code_block = code_block_pattern.search(text)

    if code_block is None:
        # code_block_pattern = re.compile(rf"(fn\s+{entry_point}.*?)(?:\n(?!\n*(?:  |\t))|$)", re.DOTALL)
        code_block_pattern = re.compile(rf"(fn\s+{entry_point}.*}})", re.DOTALL)

        code_block = code_block_pattern.search(text)
    if code_block is not None:
        return code_block.group(1)
    # if no code block is found, assume the LM is simply filling the code. Try attaching the output to the prompt
    return text

def extract_rust_code(text, item, ):

    code = extract_rust_code_block(text, item['entry_point'])
    
    pattern = r"fn\s+main\s*\(.*?\)\s*\{.*\}"
    code = re.sub(pattern, "", code, flags=re.DOTALL)

    pattern = r"fn\s+main\s*\(.*?\)\s*\{.*$"
    code = re.sub(pattern, "", code, flags=re.DOTALL)

    pattern = r"fn\s+check\s*\(.*?\)\s*\{.*\}"
    code = re.sub(pattern, "", code, flags=re.DOTALL)

    pattern = r"\s+check\s*\(.*?\)\;"
    code = re.sub(pattern, "", code, flags=re.DOTALL)

    delca_row_idx = -1
    code_lines = code.split('\n')
    code_lines = [x for x in code_lines if 'printl' not in x]


    for idx, line in enumerate(code_lines):
        if 'fn' in line  and item['entry_point'] in line:
            delca_row_idx = idx 
            break 

   
    if '{'  in code_lines[delca_row_idx] and not item['prompt'].strip().endswith('{'):
        item['prompt'] += '{'
    # print(item['prompt'])

    full_code ='\n'.join(code_lines[:delca_row_idx])+'\n' + item['prompt']+'\n' + '\n'.join(code_lines[delca_row_idx+1:])+'\n' + item['test']


    return full_code


if __name__ == '__main__':
    items = [json.loads(x) for x in open('completions_Rust_humanevalsynthesize.jsonl').readlines() if x]
    for item in items:
        extract_rust_code(item['raw_generation'][0], item)
        


        
  






