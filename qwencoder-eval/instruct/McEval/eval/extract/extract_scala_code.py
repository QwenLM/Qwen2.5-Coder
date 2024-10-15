import os 
import re 
import json 
import textwrap
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()


def extract_scala_code_block(text: str, entry_point) -> str:
    code_block_pattern = re.compile(rf"```(?:[Ss]cala\n)?.*?(def\s+{entry_point}.*?)```", re.DOTALL)
    code_block = code_block_pattern.search(text)
    if code_block is None:
        code_block_pattern = re.compile(rf"(def\s+{entry_point}.*?)(?:\n(?!\n*(?:  |\t))|$)", re.DOTALL)
        code_block = code_block_pattern.search(text)
    if code_block is not None:
        return code_block.group(1)   
    return text


def extract_scala_code(text, item, ):
    code = extract_scala_code_block(text, item['entry_point'])
    # print(code)

    
    pattern_imports = r"^import.*?$"
    pattern_imports2 = r"^from.*?import.*?$"

    # Extracting import lines from the code
    import_lines =  re.findall(pattern_imports, text, flags=re.MULTILINE)
    import_lines += re.findall(pattern_imports2, text, flags=re.MULTILINE)

    # print(import_lines)

    # Removing import lines from the code
    code = re.sub(pattern_imports, "", code, flags=re.MULTILINE).strip()
    
    pattern = r"def\s+check\s*\(.*?\).*?\{.*\}"
    code = re.sub(pattern, "", code, flags=re.DOTALL)

    pattern = r"\s+object.*?Test.*?{.*}"
    code = re.sub(pattern, "", code, flags=re.DOTALL)

    pattern = r"\s+check\s*\(.*?\)"
    code = re.sub(pattern, "", code, flags=re.DOTALL)
    
    pattern = r"\s+assert\s*\(.*\)"
    code = re.sub(pattern, "", code)

    # pattern = r"\/\/.*(\n|$)"
    # code = re.sub(pattern, "", code, flags=re.DOTALL)

    delca_row_idx = -1
    code_lines = code.split('\n')
    code_lines = [x for x in code_lines if 'println' not in x]

    for idx, line in enumerate(code_lines):
        if 'def' in line  and item['entry_point'] in line:
            delca_row_idx = idx 
            break 

    if '{'  in code_lines[delca_row_idx]:
        item['prompt'] += '{'


    full_code ='\n'.join(import_lines)+'\n'+ '\n'.join(code_lines[:delca_row_idx])+'\n' + item['prompt']+'\n' + '\n'.join(code_lines[delca_row_idx+1:])
    
    
    eql = 0
    for ch in full_code:
        if ch == '{':
            eql+=1
        elif ch == '}':
            eql-=1
    if eql == 0:
        # print(full_code)
        full_code = re.sub(r"\}\s*$", "", full_code, flags=re.DOTALL) 
        # print(full_code)
    
    full_code += '\n' + item['test']   
    return full_code


if __name__ == '__main__':
    items = [json.loads(x) for x in open('completions_Scala_humanevalsynthesize.jsonl').readlines() if x]
    for item in items:
        extract_scala_code(item['raw_generation'][0], item)
        


        
  






