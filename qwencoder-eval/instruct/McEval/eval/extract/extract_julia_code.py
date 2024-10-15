import os 
import re 
import json 
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()

def extract_julia_code_block(text: str, entry_point) -> str:
    code_block_pattern = re.compile(rf"```(?:[Jj]ulia\n)?.*?(function\s+{entry_point}.*?)\n```", re.DOTALL)
    code_block = code_block_pattern.search(text)
    if code_block is None:
        code_block_pattern = re.compile(rf"(function\s+{entry_point}.*end)", re.DOTALL)
        code_block = code_block_pattern.search(text)
    if code_block is not None:
        return code_block.group(1)
    # if no code block is found, assume the LM is simply filling the code. Try attaching the output to the prompt
    if text.startswith("def "):
        return text
    return text 

def extract_julia_code(text, item, ):
    try:
        code = extract_julia_code_block(text, item['entry_point'])
        # print(code)
        pattern_imports = r"^import.*?$"

        # Extracting import lines from the code
        import_lines = re.findall(pattern_imports, code, flags=re.MULTILINE)
        # Removing import lines from the code
        code = re.sub(pattern_imports, "", code, flags=re.MULTILINE).strip()
        

        pattern = r"\s*function\s+check\w*\(\s*\)\s*.*?\s*check\w*\(\s*\)"
        code = re.sub(pattern, "", code, flags=re.DOTALL)

        # pattern = r"\s*def\s+test\w*\(\s*\)\s*\:.*?\s*test\w*\(\s*\)"
        # code = re.sub(pattern, "", code, flags=re.DOTALL)

        pattern = r"\s*@assert.*?\n"
        code = re.sub(pattern, "", code)

        delca_col_idx = -1
        code_lines = code.split('\n')
        code_lines = [x for x in code_lines if 'println' not in x]
        for idx, line in enumerate(code_lines):
            if line.strip().startswith('function') and item['entry_point'] in line:
                delca_col_idx = idx 
                break 
        

        full_code = '\n'.join(code_lines[:delca_col_idx])+'\n' + item['prompt']+'\n'  + '\n'.join(code_lines[delca_col_idx+1:])+'\n' + item['test']

        full_code = full_code.strip().strip('julia')
    except:
        return None

    return full_code


if __name__ == '__main__':
    items = [json.loads(x) for x in open('completions_julia_humanevalsynthesize.jsonl').readlines() if x]

    for item in items:
        extract_julia_code(item['raw_generation'][0], item)
        


        
  






