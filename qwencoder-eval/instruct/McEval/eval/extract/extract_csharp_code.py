import os 
import re 
import json 
# from humanevalpack import create_all_tasks, create_task
# create_all_tasks()

def extract_csharp_code_block(text, entry_point) -> str:
    re.compile(rf"```(?:[Cc]sharp\n)?.*?({entry_point}.*?)\n```", re.DOTALL)
    code_block_pattern = re.compile(rf"```(?:[Cc]sharp)?(.*?[^\n]*?{entry_point}.*?)```", re.DOTALL)
    code_block = code_block_pattern.search(text)
        
    if code_block is None:
        code_block = re.search(rf"((?:public)?[^\n]*?{entry_point}.*)", text, flags=re.DOTALL)
    if code_block is None:
        code_block = re.search(rf"```(?:[Cc]sharp)?(.*?)\n```", text, flags=re.DOTALL)
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

def extract_csharp_code(text, item, ):

    try:
        code = extract_csharp_code_block(text, item['entry_point'])
        
        # print(code)
        pattern = r"\s*(?:public)*\s*(?:static)*\s*void\s+Main\s*\(.*?\)\s*\{.*?\n\s*\}"
        code = re.sub(pattern, "", code, flags=re.DOTALL)
        # return code
        pattern_solution_class = r"(public)*\s*class\s+\w+\s*\{\s*|\s*\}\s*$"
        # Removing the class declaration and closing brace to keep only the methods
        code = re.sub(pattern_solution_class, "\n", code, flags=re.DOTALL).strip()
        code = remove_extra_braces(code)
        # return code
        pattern_imports = r"^using.*?$"

        # Extracting import lines from the code
        import_lines = re.findall(pattern_imports, code, flags=re.MULTILINE)
        # Removing import lines from the code
        code = re.sub(pattern_imports, "", code, flags=re.MULTILINE).strip()
        
        sta_idx = code.index("{")
        code = code[sta_idx:]
        
        # return code 
        full_code = "\n".join(import_lines)+'\n' +item['prompt']+'\n'+ code 
        eql = 0
        for ch in full_code:
            if ch == '{':
                eql+=1
            elif ch == '}':
                eql-=1
        full_code += '\n}'* (eql-1)
            
        full_code += '\n' + item['test']
    except:
        return "" 
    # print(full_code)
    return full_code


if __name__ == '__main__':
    items = [json.loads(x) for x in open('completions_C_sharp_humanevalsynthesize.jsonl').readlines() if x]

    for item in items:
        extract_csharp_code(item['raw_generation'][0], item)
        


        
  






