import json
import os

extension_dic = {'Common Lisp': 'lisp',
                 'Emacs Lisp': "el", 'Elixir': 'exs', 'Racket': 'rkt', 'Scheme': 'scm', 'Haskell': 'hs', 'Shell': 'sh', 'PowerShell': 'ps1', 'Swift': 'swift', 'Perl': 'pl', 'Tcl': 'tcl',
                'Python': 'py',
                'python': 'py',
                'julia': 'jl',
                'Julia': 'jl',
                'coffee': 'coffee',
                'CoffeeScript': 'coffee',
                'Coffeescript': 'coffee',
                'kotlin': 'kts',
                'Kotlin': 'kts',
                'php': 'php',
                'PHP': 'php',
                'r': 'R',
                'R': 'R',
                'Visual Basic':'vb',
                'ruby': 'rb',
                'Ruby': 'rb',
                'Java': 'java',
                'java': 'java',
                'cs': 'cs',
                'C_sharp': 'cs',
                'C#': 'cs',
                'F#': 'fs',
                # 'fortran': 'f95',
                'Fortran': 'f95',
                'fortran': 'f95',
                'Rust': 'rs',
                'rust': 'rs',
                'scala': 'scala',
                'Scala': 'scala',
                'Dart': 'dart',
                'dart': 'dart',
                'groovy': 'groovy',
                'Groovy': 'groovy',
                'C': 'c',
                'CPP': 'cpp',
                'Go': 'go',
                'JavaScript': 'js',
                'TypeScript': 'ts',
                'VimScript': 'vim',
                'Lua': 'lua',
                'Pascal': 'pas',
                'JSON': 'json',
                'Markdown': 'md',
                'HTML': 'html'
                 }


def read_jsonl(file):
    data = []
    with open(file, 'r') as f:
        for line in f:
            data.append(json.loads(line))
    return data


def save2file(content, language_type, item):
    task_id = item['task_id']
    task_id = task_id.split('/')[-1]

    if language_type == 'Visual Basic':
        # content = f"{line['prompt']}\n\n{line['canonical_solution']}\n\n{line['test']}"
        output_file = '../data/Visual Basic/APP/Program.vb'
        with open('./tmp/' + task_id + '.' + extension_dic[language_type], 'w') as f:
            f.write(content)
    elif language_type == 'F#':
        # content = f"{line['prompt']}\n\n{line['canonical_solution']}\n\n{line['test']}"
        output_file = '../data/F#/MyFsharpApp/Program.fs'

        with open('./tmp/' + task_id + '.' + extension_dic[language_type], 'w') as f:
            f.write(content)
    elif language_type in ['cs', 'C_sharp', 'C#']: # C#
        # content = f"{line['prompt']}\n\n{line['canonical_solution']}\n\n{line['test']}"
        output_file = '../data/C#/MyConsoleApp/Program.cs'
        with open('./tmp/' + task_id + '.' + extension_dic[language_type], 'w') as f:
            f.write(content)


    elif language_type == 'Rust':  # C#
        # content = f"{line['prompt']}\n\n{line['canonical_solution']}\n\n{line['test']}"
        output_file = '../data/rust/src/main.rs'
        with open('./tmp/' + task_id + '.' + extension_dic[language_type], 'w') as f:
            f.write(content)
        # output_file = 'tmp' + '/' + task_id + '.' + extension_dic[language_type]
    elif language_type == 'AWK':
        return content, language_type, task_id
        # TODO
    elif language_type == 'Erlang':
        # content = f"{line['prompt']}\n\n{line['canonical_solution']}\n\n{line['test']}"
        output_file = 'tmp' + '/' + item['module'] + '.erl'
        # output_file = 'tmp' # TODO

        # TODO
    elif language_type.lower() == 'fortran':
        # content = f"{line['test']}\n\n{line['prompt']}\n\n{line['canonical_solution']}"
        # 写入文件
        output_file = 'tmp' + '/' + task_id + \
            '.' + extension_dic[language_type]
    elif language_type.lower() == 'go':
        # content = f"{line['prompt']}\n\n{line['canonical_solution']}\n\n{line['test']}"
        # 写入文件
        output_file = 'tmp' + '/' + task_id+'_test' + \
            '.' + extension_dic[language_type]   
        # output_file = 'data/go/' + task_id+'_test' + '.' + extension_dic[language_type]
    else:
        # content = f"{line['prompt']}\n\n{line['canonical_solution']}\n\n{line['test']}"
        # 写入文件
        output_file = 'tmp' + '/' + task_id + \
            '.' + extension_dic[language_type]

    if language_type != "AWK":
        if not os.path.exists(os.path.dirname(output_file)):
            os.makedirs(os.path.dirname(output_file))
        if language_type == 'VimScript':
            with open(output_file, 'w', encoding='utf-8') as f:
                content = content.replace('\r\n', '\n')
                f.write(content)
        else:
            with open(output_file, 'w') as f:
                f.write(content)
    print(f'代码已成功转换为{language_type}文件，并保存到 {output_file}')
    return output_file, language_type, task_id




def save2file_with_tempdir(content, language_type, item, temp_dir):
    task_id = item['task_id']
    task_id = task_id.split('/')[-1]

    if language_type == 'Visual Basic':
        output_file = os.path.join(temp_dir, 'Visual Basic/APP/Program.vb')
        with open( os.path.join(temp_dir, task_id + '.' + extension_dic[language_type]), 'w') as f:
            f.write(content)
    elif language_type == 'F#':
        output_file = os.path.join(temp_dir, 'F#/MyFsharpApp/Program.fs')
        with open( os.path.join(temp_dir, task_id + '.' + extension_dic[language_type]), 'w') as f:
            f.write(content)
    elif language_type in ['cs', 'C_sharp', 'C#']: # C#
        output_file = os.path.join(temp_dir,  'C#/MyConsoleApp/Program.cs')
        with open( os.path.join(temp_dir, task_id + '.' + extension_dic[language_type]), 'w') as f:
            f.write(content)

    elif language_type == 'Rust':  # C#
        output_file =  os.path.join(temp_dir, 'rust/src/main.rs')
        with open( os.path.join(temp_dir, task_id + '.' + extension_dic[language_type]), 'w') as f:
            f.write(content)
      
    elif language_type == 'AWK':
        return content, language_type, task_id
       
    elif language_type == 'Erlang':
        output_file = os.path.join(temp_dir, item['module'] + '.erl')
      
    elif language_type.lower() == 'fortran':
        # 写入文件
        output_file =   os.path.join(temp_dir, task_id + '.' + extension_dic[language_type])
    elif language_type.lower() == 'go':
        # 写入文件
        output_file =  os.path.join(temp_dir, task_id+'_test' + '.' + extension_dic[language_type])  
    else:
        # 写入文件
        output_file = os.path.join(temp_dir, task_id + \
            '.' + extension_dic[language_type])

    if language_type != "AWK":
        if not os.path.exists(os.path.dirname(output_file)):
            os.makedirs(os.path.dirname(output_file))
        if language_type == 'VimScript':
            with open(output_file, 'w', encoding='utf-8') as f:
                content = content.replace('\r\n', '\n')
                f.write(content)
        else:
            with open(output_file, 'w') as f:
                f.write(content)
    print(f'代码已成功转换为{language_type}文件，并保存到 {output_file}')
    return output_file, language_type, task_id
