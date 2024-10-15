import os 
import re 
import json 
import textwrap
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()


def extract_php_code_block(text: str, entry_point) -> str:
    code_block_pattern = re.compile(rf"```(?:[pP]hp\n)?.*?(function\s+{entry_point}.*?)\n```", re.DOTALL)
    code_block = code_block_pattern.search(text)
    if code_block is None:
        code_block_pattern = re.compile(rf"(function\s+{entry_point}.*}})", re.DOTALL)
        code_block = code_block_pattern.search(text)
    if code_block is not None:
        return code_block.group(1)
    # if no code block is found, assume the LM is simply filling the code. Try attaching the output to the prompt
    return text


def extract_php_code(text, item):

    code = extract_php_code_block(text, item['entry_point'])
    
    # print(code)
 
    pattern_imports = r"^import.*?$"
    # pattern_imports2 = r"^from.*?import.*?$"

    # Extracting import lines from the code
    # import_lines =  re.findall(pattern_imports, code, flags=re.MULTILINE)
    # import_lines += re.findall(pattern_imports2, code, flags=re.MULTILINE)

    # Removing import lines from the code
    # code = re.sub(pattern_imports, "", code, flags=re.MULTILINE).strip()
    
    delca_row_idx = -1


    pattern = r"function\s+check\w*\(.*?\)\s*\{.*\}"
    code = re.sub(pattern, "", code, flags=re.DOTALL)
    pattern = r"\s*check\w*\(.*?\)\s*\;"
    code = re.sub(pattern, "", code, flags=re.DOTALL)
    
    pattern = r"\?\>"
    code = re.sub(pattern, "", code, flags=re.DOTALL)
    

    code_lines = code.split('\n')
    code_lines = [x for x in code_lines if 'echo' not in x]

    for idx, line in enumerate(code_lines):
        if 'function' in line  and item['entry_point'] in line:
            delca_row_idx = idx 
            # print(delca_row_idx, line)
            break 

    
    

    if '{'  in code_lines[delca_row_idx]:
        item['prompt'] += '{'

    # print('\n'.join(code_lines[:delca_row_idx]))

    full_code = item['prompt']+'\n' + '\n'.join(code_lines[:delca_row_idx])+'\n' +'\n'.join(code_lines[delca_row_idx+1:])+'\n' + item['test']

    # print(full_code)
    return full_code


if __name__ == '__main__':
    items = [json.loads(x) for x in open('completions_PHP_humanevalsynthesize.jsonl').readlines() if x]
    for item in items:
        extract_php_code(item['raw_generation'][0], item)
        


        
  






