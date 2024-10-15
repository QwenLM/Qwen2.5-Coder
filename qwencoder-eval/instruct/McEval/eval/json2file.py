import json
import shutil 
extension_dic = {'Common Lisp': 'lisp',
                 'Emacs Lisp': "el", 'Elixir': 'exs', 'Racket': 'rkt', 'Scheme': 'scm', 'Haskell': 'hs', 'Shell': 'sh', 'PowerShell': 'ps1', 'Swift': 'swift', 'Perl': 'pl', 'Tcl': 'tcl',
                 'Python': 'py',
                 'sql': 'py',
                 'julia': 'jl',
                 'coffee': 'coffee',
                 'kotlin': 'kts',
                 'php': 'php',
                 'r': 'R',
                 'ruby': 'rb',
                 'Java': 'java',
                 'cs': 'cs',
                 'fortran': 'f95',
                 'Rust': 'rs',
                 'scala': 'scala',
                 'dart': 'dart',
                 'groovy': 'groovy',
                 'C': 'c',
                 'CPP': 'cpp',
                 'Go': 'go',
                 'JavaScript': 'js',
                 'TypeScript': 'ts',
                 'VimScript': 'vim',
                 'Lua': 'lua',
                 'Pascal': 'pas',
                 }

def read_jsonl(file):
    data = []
    with open(file, 'r') as f:
        for line in f:
            data.append(json.loads(line))
    return data


def json2file(line):
    language_type = line['task_id'].split('/')[0]
    task_id = line['task_id'].split('/')[1]
    if language_type == 'Visual Basic':
        content = f"{line['prompt']}\n\n{line['canonical_solution']}\n\n{line['test']}"
        output_file = '../data/Visual Basic/APP/Program.vb'
    elif language_type == 'F#':
        content = f"{line['prompt']}\n\n{line['canonical_solution']}\n\n{line['test']}"
        output_file = '../data/F#/MyFsharpApp/Program.fs'
    elif language_type == 'cs':  # C#
        content = f"{line['prompt']}\n\n{line['canonical_solution']}\n\n{line['test']}"
        output_file = '../data/C#/MyConsoleApp/Program.cs'
    elif language_type == 'Rust':  # C#
        content = f"{line['prompt']}\n\n{line['canonical_solution']}\n\n{line['test']}"
        output_file = '../data/rust/src/main.rs'
        with open('./tmp/' + task_id + '.' + extension_dic[language_type], 'w') as f:
            f.write(content)
        # output_file = 'tmp' + '/' + task_id + '.' + extension_dic[language_type]
    elif language_type == 'AWK':
        output_file = line['canonical_solution']
    elif language_type == 'Erlang':
        content = f"{line['prompt']}\n\n{line['canonical_solution']}\n\n{line['test']}"
        output_file = 'tmp' + '/' + line['module'] + '.erl'
    elif language_type == 'fortran':
        content = f"{line['test']}\n\n{line['prompt']}\n\n{line['canonical_solution']}"
        # 写入文件
        output_file = 'tmp' + '/' + task_id + \
            '.' + extension_dic[language_type]
    elif language_type == 'Go':
        content = f"{line['prompt']}\n\n{line['canonical_solution']}\n\n{line['test']}"
        # 写入文件
        # output_file = 'tmp' + '/' + task_id+'_test' + '.' + extension_dic[language_type]
        output_file = '../data/go/' + task_id+'_test' + \
            '.' + extension_dic[language_type]
    
    elif language_type == 'HTML':
        task_id = line['task_id'].split('/')[1]
        output_file = f'tmp/{task_id}.html'
        shutil.copyfile(f'../data/HTML/{task_id}.html', output_file)
    elif language_type == 'JSON':
        task_id = line['task_id'].split('/')[1]
        output_file = f'tmp/{task_id}.json'
        shutil.copyfile(f'../data/JSON/{task_id}.json', output_file)
    elif language_type == 'Markdown':
        task_id = line['task_id'].split('/')[1]
        output_file = f'tmp/{task_id}.md'
        shutil.copyfile(f'../data/Markdown/{task_id}.md', output_file)
    else:
        content = f"{line['prompt']}\n\n{line['canonical_solution']}\n\n{line['test']}"
        # 写入文件
        output_file = 'tmp' + '/' + task_id + \
            '.' + extension_dic[language_type]

    if language_type not in ["AWK", 'HTML', 'Markdown', 'JSON']:
        with open(output_file, 'w') as f:
            f.write(content)
    print(f'JSONL数据已成功转换为{language_type}文件，并保存到 {output_file}')
    return output_file, language_type, line['task_id']
