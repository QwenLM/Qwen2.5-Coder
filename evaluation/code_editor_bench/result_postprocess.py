import json
import jsonlines
import re
import pdb
import os

def count_code_language(dataset):
    path = f'data/code_{dataset}.jsonl'
    data = read_jsonl_file(path)
    lang_count = {}
    for d in data:
        if dataset == 'debug':
            lang = d['code_language']
        elif dataset == 'translate':
            lang = d['target_lang']
        elif dataset == 'polish':
            lang = d['source_lang']
        elif dataset == 'switch':
            lang = d['language']
        else:
            print("Invalid dataset!")
        if lang in lang_count:
            lang_count[lang] += 1
        else:
            lang_count[lang] = 1
    print(lang_count)    

def read_jsonl_file(file_path):
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def extract_from_first_keyword(code, code_keywords):
    keywords_pattern = r'\b(' + '|'.join(re.escape(keyword) for keyword in code_keywords) + r')\b'
    print(keywords_pattern)
    
    # Search the first key word
    match = re.search(keywords_pattern, code)

    if match:
        start_index = match.start()
        # Search the first two consecutive newlines after the first key word
        end_index = code.find('\n\n', start_index)
        if end_index == -1:
            # If there is no two consecutive newlines after the first key word, search the first newline after the first key word
            end_index = len(code)
        return code[start_index:end_index]
    # If there is no key word, return the whole code

    return ""

def preprocess(raw_code, code_keywords):
    sign = 'corrected code'
    if raw_code.strip().startswith('```') and not any(keyword in raw_code[:50] for keyword in code_keywords):
        raw_code = raw_code[3:]
    if sign in raw_code[:50].lower():
        begin = raw_code.lower().find(sign)
        raw_code = raw_code[begin + len(sign):]

    return raw_code

def extract_code_first(raw_code):
    pattern = '```(?:[\w\+]*)\r?\n?([\s\S]*?)\r?\n?```'
    # Search the first code block
    match = re.search(pattern, raw_code)
    not_found = 0
    if match:
        raw_code = match.group(1).strip()
    else:
        not_found = 1

    return raw_code, not_found

def extract_code_pattern1(raw_code):
    # Extract this pattern: cpp\n ... }\n\n
    not_found = 0
    regex = r"(?i)(C\+\+|Python|Java|cpp|c\+\+|python|python3|java)\n(.*\})\n\n"
    matches = re.findall(regex, raw_code, re.DOTALL)
    assert len(matches) <= 1
    if matches:
        for match in matches:
            language = match[0]
            raw_code = match[1]
    else:
        not_found = 1

    return raw_code, not_found

def extract_code_pattern2(raw_code, language_words):
    # Extract this pattern: cpp\n ...

    not_found = 0
    language_pattern = '|'.join([re.escape(word) for word in language_words])

    regex = rf"(?i)({language_pattern})\n([\s\S]*)"
    match = re.search(regex, raw_code)

    if match:
        language = match.group(1)
        raw_code = match.group(2)

    else:
        not_found = 1
    
    return raw_code, not_found

def extract_code_pattern3(raw_code, code_keywords):
    # Extract this pattern: #include and other identifiers to ... }\n\n
    not_found = 0
    escaped_keywords = [re.escape(keyword) for keyword in code_keywords]
    keywords_regex = '|'.join(escaped_keywords)
    
    # Search for all keywords
    matches = list(re.finditer(keywords_regex, raw_code))
    if not matches:
        not_found = 1
        return "", not_found
    
    # Find the first keyword
    first_match_start = min(match.start() for match in matches)
    
    # Find all `}\n\n` after the first keyword
    code_end_matches = list(re.finditer(r"\}\n\n", raw_code))
    if not code_end_matches:
        # If there is no `}\n\n` after the first keyword, return the whole code
        not_found = 1
        return raw_code[first_match_start:], not_found

    # Find the last `}\n\n` after the first keyword
    last_match_end = code_end_matches[-1].end()

    # If the last `}\n\n` is before the first keyword, return the whole code
    if last_match_end < first_match_start:
        not_found = 1
        return raw_code[first_match_start:], not_found
    
    return raw_code[first_match_start:last_match_end], not_found
    

def filter_code(raw_code, type, file_path):
    code_keywords = ['#include', 'include', 'from', 'import', 'class', 'Class', 'void', 'int', 'main', 'const', 'double', 'bool', 'float',
                    'char', 'long', 'struct', 'public', 'private', 'protected', 'static', 'final', 'abstract',
                    'interface', 'extends', 'implements', 'package', 'namespace', 'using', 'def', 'return', 'if',
                    'else', 'elif', 'for', 'while', 'do', 'switch', 'case', 'break', 'continue', 'try', 'catch',
                    'throw', 'finally', 'assert', 'new', 'delete', 'super', 'self', 'true', 'false', 'null',
                    'None', 'nil', 'print', 'println', 'cout', 'cin', 'scanf', 'printf', 'scanf', '=', '/usr/bin', 'utf-8', '####']
    language_words = ['C++', 'Python', 'Java', 'cpp', 'c++', 'python', 'python3', 'java']
    original_code = raw_code

    not_found = 0

    if type == "zero":
        raw_code = preprocess(raw_code, code_keywords)
        raw_code, not_found = extract_code_first(raw_code) # extract the first code block
        if not_found == 0:
            code = raw_code
        else:
            # not_found is 1 here, so we need to set it to 0 after extracting the code successfully
            if file_path == 'CodeFuse_CodeLlama_34B_0_end.jsonl':
                raw_code, not_found = extract_code_pattern1(raw_code)
                if not_found == 0:
                    code = raw_code
                else:
                    raw_code, not_found = extract_code_pattern2(raw_code, language_words)
                    if not_found == 0:
                        code = raw_code
                    else:
                        code, not_found = extract_code_pattern3(raw_code, code_keywords)
            else:
                # not_found is 1 here
                code = raw_code
                assert not_found == 1
                not_found = 1
                # print(f"Original Code:\n{original_code!r}\n")
                # print(f"Raw Code:\n{raw_code!r}\n")
                # pdb.set_trace()


    elif type == "other":
        raw_code = preprocess(raw_code, code_keywords)
        raw_code, not_found = extract_code_first(raw_code)
        if not_found == 0:
            code = raw_code
        else:    
            # If code starts with cpp, python, java, etc., filter it out
            raw_code = raw_code.strip()
            # If code starts with ```, remove it
            if raw_code.startswith('```'):
                raw_code = raw_code.split('```')[1]
            for word in language_words:
                if raw_code.startswith(word):
                    raw_code = raw_code[len(word):].lstrip()

            raw_code, not_found = extract_code_pattern3(raw_code, code_keywords)
            if not_found == 0:
                code = raw_code
            else:
                code = raw_code.strip()
                if len(code) > 0 and code[-1] == '}':
                    not_found = 0
                # else:
                #     print(f"Original Code:\n{original_code!r}\n")
                #     print(f"Raw Code:\n{raw_code!r}\n")
                #     pdb.set_trace()


    else:
        raw_code = preprocess(raw_code, code_keywords)
        raw_code, not_found = extract_code_first(raw_code)
        if not_found == 0:
            code = raw_code
        else:
            # not_found is 1 here, so we need to set it to 0 after extracting the code successfully
            raw_code = raw_code.strip()
            if '```' in raw_code:
                code = raw_code.split('```')[1]
                not_found = 0
            else:
                raw_code, not_found = extract_code_pattern3(raw_code, code_keywords)
                if not_found == 0:
                    code = raw_code
                else:
                    # print(f"Original Code:\n{original_code!r}\n")
                    # print(f"Raw Code:\n{raw_code!r}\n")
                    # pdb.set_trace()
                    code = raw_code.strip()
                    assert not_found == 1
                    not_found = 1
    
    return code.strip(), not_found

if __name__ == "__main__":
    datasets = ['debug', 'translate', 'polish', 'switch']
    for dataset in datasets:
        file_dir = f'greedy_result/code_{dataset}/'
        file_paths = [f for f in os.listdir(file_dir) if os.path.isfile(os.path.join(file_dir, f))]
        for file_path in file_paths:
            total_not_found = 0
            print(file_path)
            data = read_jsonl_file(file_dir+file_path)
            with open(f'solution_folder/code_{dataset}/{file_path}', 'w') as f:
                for idx, d in enumerate(data[1:]):
                    try:
                        # assert len(d['code']) == 20  # 20 completions
                        assert len(d['code']) == 1
                    except:
                        # print(f"File: {file_path}")
                        print(f"Code length: {len(d['code'])}")
                        # pdb.set_trace()
                        # d['code'] = " " * 20
                        d['code'] = " "
                    # for i in range(20):
                    for i in range(1):
                        new_dict = {}
                        for key, value in d.items():
                            if key == 'code':
                                raw_code = value[i]
                                if "Few_Shot" in file_path:
                                    type = "three"
                                elif file_path == 'octocoder_0_end.jsonl' or file_path == 'CodeLlama_34b_hf_0_end.jsonl':
                                    type = "other"
                                else:
                                    type = "zero"
                                new_dict[key], not_found = filter_code(raw_code, type, file_path)
                                total_not_found += not_found
                            elif key == 'completion_id':
                                new_dict[key] = i
                            elif key == 'language' or key == 'source_lang' or key == 'target_lang':
                                if value == 'cpp' or value == 'c++':
                                    new_dict[key] = 'C++'
                                elif value == 'python' or value == 'python3':
                                    new_dict[key] = 'Python'
                                elif value == 'java':
                                    new_dict[key] = 'Java'
                                else:
                                    raise ValueError(f"Invalid language: {value}")
                            else:
                                new_dict[key] = value
                        f.write(json.dumps(new_dict) + '\n')
                print(f"Type: {type}")
            print(f"Total not found: {total_not_found}")
            # pdb.set_trace()

     
