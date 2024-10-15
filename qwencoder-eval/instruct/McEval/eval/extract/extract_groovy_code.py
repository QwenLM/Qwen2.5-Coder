import os 
import re 
import json 
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()

def extract_groovy_code_block(text, entry_point) -> str:
    re.compile(rf"```(?:[Gg]roovy\n)?.*?({entry_point}.*?)\n```", re.DOTALL)
    code_block_pattern = re.compile(rf"```(?:[Gg]roovy)?(.*?public[^\n]*?{entry_point}.*?)```", re.DOTALL)
    code_block = code_block_pattern.search(text)

        
    if code_block is None:
        code_block = re.search(rf"(public[^\n]*?{entry_point}.*)", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(rf"```(?:[Gg]roovy)?(.*?)\n```", text, flags=re.DOTALL)
    if code_block is None:
        return text
    else:
        return code_block.group(1)

def extract_groovy_code(text, item):

    try:
        code = extract_groovy_code_block(text, item['entry_point'])
    
        code_lines = code.split('\n')
        code_lines = [x for x in code_lines if 'println' not in x]
        
        example_row_idx = -1
        for idx, line in enumerate(code_lines):
            if '//' in line and ('usage' in line.lower() or 'example' in line.lower() ):
                example_row_idx = idx 
        if example_row_idx >0 :
            code_lines = code_lines[:example_row_idx]    
        code = '\n'.join(code_lines)
        
        if not item.get('extract', True):
            code += '\n' + item['test']
            return code 
            
        pattern = r"\s*(?:public)*\s+static\s+void\s+main\s*\(String\[\]\s+args\)\s*\{.*?\n\s*\}"
        code = re.sub(pattern, "", code, flags=re.DOTALL)

        pattern = r"\s*(?:def)*\s*(?:static)*\s*(?:void)*\s+check\s*\(\s*\)\s*\{.*?\n\s*\}"
        code = re.sub(pattern, "", code, flags=re.DOTALL)

        pattern = r"\s*check\s*\(\s*\)\s*"
        code = re.sub(pattern, "", code, flags=re.DOTALL)

        pattern = r"\s*assert\s+.*?\n"
        code = re.sub(pattern, "", code, flags=re.DOTALL)

        pattern_solution_class = r"(?:public)*\s*class\s+\w+\s*\{\s*|\s*\}\s*$"
        # Removing the class declaration and closing brace to keep only the methods
        code = re.sub(pattern_solution_class, "\n", code, flags=re.DOTALL).strip()
        
        pattern_imports = r"^import.*?$"

        # Extracting import lines from the code
        import_lines = re.findall(pattern_imports, code, flags=re.MULTILINE)
        # Removing import lines from the code
        code = re.sub(pattern_imports, "", code, flags=re.MULTILINE).strip()

        sta_idx = code.index("{")
        code = code[sta_idx+1:]
        
        full_code = "\n".join(import_lines)+'\n' +item['prompt']+'\n'+ code 
        eql = 0
        for ch in full_code:
            if ch == '{':
                eql+=1
            elif ch == '}':
                eql-=1
        full_code += '\n}'* eql
            

            # code +='\n'+'}'
        
        full_code += '\n' + item['test']
        # print(full_code)
        return full_code
    except:
        return ""

if __name__ == '__main__':

    items = [json.loads(x) for x in open('completions_groovy_humanevalsynthesize.jsonl').readlines() if x]
    for item in items:
        extract_groovy_code(item['raw_generation'][0], item)
  
        


        
  






