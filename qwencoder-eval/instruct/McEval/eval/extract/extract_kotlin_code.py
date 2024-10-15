import os 
import re 
import json 
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()

def extract_kotlin_code_block(text, entry_point) -> str:

    code_block_pattern = re.compile(rf"```(?:[Kk]otlin)?(.*?[^\n]*?{entry_point}.*?)```", re.DOTALL)
    code_block = code_block_pattern.search(text)

    if code_block is None:
        code_block = re.search(rf"([^\n]*?{entry_point}.*)", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(rf"```(?:[Kk]otlin)?(.*?)\n```", text, flags=re.DOTALL)
    if code_block is None:
        return text
    else:
        return code_block.group(1)

def remove_extra_braces(code):
    stack = []
    result = ''
    for char in code:
        if char == '{':
            stack.append(char)
        elif char == '}':
            if stack:
                stack.pop()
            else:
                # 遇到多余的}时不添加到结果字符串中
                continue
        result += char
    return result

def extract_kotlin_code(text, item, ):

    try:
        code = extract_kotlin_code_block(text, item['entry_point'])
        # print(code)
        
        pattern = r"\s*fun\s+main\s*\(\s*\)\s*\{.*?\n\s*\}"
        code = re.sub(pattern, "", code, flags=re.DOTALL)

        pattern = r"\s*fun\s+check\w*\s*\(\s*\)\s*\{.*?\n\s*\}"
        code = re.sub(pattern, "", code, flags=re.DOTALL)

        pattern = r"\s*check\w*\s*\(\s*\)"
        code = re.sub(pattern, "", code, flags=re.DOTALL)

        code = remove_extra_braces(code)
        # pattern_solution_class = r"public\s+class\s+\w+\s*\{\s*|\s*\}\s*$"
        # # Removing the class declaration and closing brace to keep only the methods
        # code = re.sub(pattern_solution_class, "", code, flags=re.DOTALL).strip()
    
        pattern_imports = r"^import.*?$"

        # Extracting import lines from the code
        import_lines = re.findall(pattern_imports, code, flags=re.MULTILINE)
        # Removing import lines from the code
        code = re.sub(pattern_imports, "", code, flags=re.MULTILINE).strip()

        # code = code.split(item['entry_point'])[-1]
        # print(code)
        # print(code.index("{"))
        sta_idx = code.index("{")
        code = code[sta_idx:]


        full_code = "\n".join(import_lines)+'\n' +item['prompt']+'\n'+ code+'\n' + item['test']
    except:
        return None 
    # print(full_code)
    return full_code


if __name__ == '__main__':
    items = [json.loads(x) for x in open('completions_kotlin_humanevalsynthesize.jsonl').readlines() if x]

    for item in items:
        extract_kotlin_code(item['raw_generation'][0], item)
        


        
  






