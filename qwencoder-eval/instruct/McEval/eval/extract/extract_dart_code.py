import os 
import re 
import json 
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()

def extract_dart_code_block(text, entry_point) -> str:
    re.compile(rf"```(?:[Dd]art\n)?.*?({entry_point}.*?)\n```", re.DOTALL)
    code_block_pattern = re.compile(rf"```(?:[Dd]art)?(.*?[^\n]*?{entry_point}.*?)```", re.DOTALL)
    code_block = code_block_pattern.search(text)

        
    if code_block is None:
        code_block = re.search(rf"((?:public)?[^\n]*?{entry_point}.*)", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(rf"```(?:[Dd]art)?(.*?)\n```", text, flags=re.DOTALL)

    if code_block is None:
        code_block_pattern = re.compile(rf"(\n.*?\s+{entry_point}.*}})", re.DOTALL)
        code_block = code_block_pattern.search(text)
    if code_block is None:
        return text
    else:
        return code_block.group(1)

def extract_dart_code(text, item, ):
    try:
        code = extract_dart_code_block(text, item['entry_point'])
        
        pattern = r"\s*(public)*\s*(static)*\s*void\s+main\s*\(\s*\)\s*\{.*?\n\s*\}"
        code = re.sub(pattern, "", code, flags=re.DOTALL)
        
        # pattern_solution_class = r"(public)*\s*class\s+\w+\s*\{\s*|\s*\}\s*$"
        # # Removing the class declaration and closing brace to keep only the methods
        # code = re.sub(pattern_solution_class, "\n", code, flags=re.DOTALL).strip()
    
        pattern_imports = r"^import.*?$"

        # Extracting import lines from the code
        import_lines = re.findall(pattern_imports, code, flags=re.MULTILINE)
        # Removing import lines from the code
        code = re.sub(pattern_imports, "", code, flags=re.MULTILINE).strip()
        # print(code)
        # code = code.split(item['entry_point'])[-1]
        # print(code)
        # print(code.index("{"))
        sta_idx = code.index("{")
        code = code[sta_idx:]

        full_code = "\n".join(import_lines)+'\n' +item['prompt']+'\n'+ code+'\n' + item['test']
        return full_code
    except:
        return "" 


        


        
  






