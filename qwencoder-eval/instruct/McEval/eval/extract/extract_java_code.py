import os 
import re 
import json 
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()

def extract_java_code_block(text, entry_point) -> str:
    re.compile(rf"```(?:[Jj]ava\n)?.*?({entry_point}.*?)\n```", re.DOTALL)
    code_block_pattern = re.compile(rf"```(?:[Jj]ava)?(.*?[^\n]*?{entry_point}.*?)```", re.DOTALL)
    code_block = code_block_pattern.search(text)

    if code_block is None:
        code_block = re.search(rf"((?:public)?[^\n]*?{entry_point}.*)", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(rf"```(?:[Jj]ava)?(.*?)\n```", text, flags=re.DOTALL)
    if code_block is None:
        return text
    else:
        return code_block.group(1)

def extract_java_code(text, item):
    # task = create_task('java', 'synthesize')(language='java')
    # pattern = r"\s*public static void main\(String\[\] args\) \{.*?\n\s*\}"
   

        
    # print('='*50)
    # print(item['task_id'])
    # print(item['prompt'])


    code = extract_java_code_block(text, item['entry_point'])
        # # print(content)
    # print(code)
        
    pattern = r"\s*public\s+static\s+void\s+main\s*\(String\[\]\s+args\)\s*\{.*?\n\s*\}"
    code = re.sub(pattern, "", code, flags=re.DOTALL)
    pattern_solution_class = r"public\s+class\s+\w+\s*\{\s*|\s*\}\s*$"
    # Removing the class declaration and closing brace to keep only the methods
    code = re.sub(pattern_solution_class, "\n", code, flags=re.DOTALL).strip()
    
    pattern_imports = r"^import.*?$"

    # Extracting import lines from the code
    import_lines = re.findall(pattern_imports, code, flags=re.MULTILINE)
    # Removing import lines from the code
    code = re.sub(pattern_imports, "", code, flags=re.MULTILINE).strip()

    try:
        sta_idx = code.index("{")
        code = code[sta_idx:]
    except:
        return ""
     
    full_code = "\n".join(import_lines)+'\n' +item['prompt']+'\n'+ code 
    eql = 0
    for ch in full_code:
        if ch == '{':
            eql+=1
        elif ch == '}':
            eql-=1
    full_code += '\n}'* (eql-1)
        
    full_code += '\n' + item['test']

    return full_code


if __name__ == '__main__':

    items = [json.loads(x) for x in open('completions_java_humanevalsynthesize.jsonl').readlines() if x]
    extract_java_code()
  
        


        
  






