import os 
import re 
import json 
import textwrap
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()


def extract_fortran_code_block(text: str, entry_point) -> str:
    code_block_pattern = re.compile(rf"```(?:[Ff]ortran\n)?(.*?{entry_point}.*?)\n```", re.DOTALL)
    code_block = code_block_pattern.search(text)
    if code_block is None:
        code_block_pattern = re.compile(rf"(function\s+{entry_point}.*?end\s+function\s+{entry_point})", re.DOTALL)
        code_block = code_block_pattern.search(text)
        
    if code_block is None:
        code_block_pattern = re.compile(rf"(subroutine\s+{entry_point}.*?end\s+subroutine\s+{entry_point})", re.DOTALL)
        code_block = code_block_pattern.search(text)
        
    if code_block is not None:
        return code_block.group(1)
    # if no code block is found, assume the LM is simply filling the code. Try attaching the output to the prompt
    return text


def extract_fortran_code(text, item, ):

    code = extract_fortran_code_block(text, item['entry_point'])
    print(code)


    pattern_func = r"(?:\b(?:recursive|pure|elemental|integer|logical)\s+)?function\s+.*?end\s+function\s+\b(?:\w+)\b"
    pattern_subrt = r"(?:\b(?:recursive|pure|elemental|integer|logical)\s+)?subroutine\s+.*?end\s+subroutine\s+\b(?:\w+)\b"

    # Removing import lines from the code
    funcs = re.findall(pattern_func, code, flags=re.DOTALL)
    subrts = re.findall(pattern_subrt, code, flags=re.DOTALL)

    print(funcs)


    code = '\n'.join(funcs)+'\n'+'\n'.join(subrts)
    # print(code)
    delca_row_idx = -1
    code_lines = code.split('\n')
    code_lines = [x for x in code_lines if 'print' not in x]

    for idx, line in enumerate(code_lines):
        if ('function' in line or 'subroutine' in line ) and item['entry_point'] in line:
            delca_row_idx = idx 
            break 

    
    # main_row_idx = -1
    # remove main part
    # for idx, line in enumerate(code_lines):
    #     if '__main__'in line:
    #         main_row_idx = idx 
    #         break 
    # if main_row_idx > 0:
    #     code_lines = code_lines[:main_row_idx]

    # if '{'  in code_lines[delca_row_idx]:
    #     item['prompt'] += '{'
    # print(code)

    full_code =item['test']+'\n'+ '\n'.join(code_lines[:delca_row_idx])+'\n' + item['prompt']+'\n' + '\n'.join(code_lines[delca_row_idx+1:])+'\n' +'end program main'

    # print(full_code)
    return full_code


if __name__ == '__main__':
    items = [json.loads(x) for x in open('completions_fortran_humanevalsynthesize.jsonl').readlines() if x]
    for item in items:
        extract_fortran_code(item['raw_generation'][0], item)
        


        
  






