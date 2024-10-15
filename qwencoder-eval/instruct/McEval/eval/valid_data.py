from json2file import read_jsonl, json2file
from excute import excute
from excute import get_awk_ans
import os 
import glob


def valid_label():
    data_path ='/workspace/MMCodeEval/data'
    beam_path = '/workspace/MMCodeEval/eval'
    tmp_path = '/workspace/MMCodeEval/tmp'
    langs = ['Haskell', 'CPP', 'HTML', 'rust', 'coffeescript', 'Racket', 'PowerShell', 'Swift', 'VimScript', 'groovy', 'TypeScript', 'SQL', 'Emacs Lisp', 'fortran', 'kotlin', 'Shell', 'JSON', 'Pascal', 'ruby', 'F#', 'R', 'Elixir', 'C#', 'Lua', 'dart', 'Visual Basic', 'JAVA', 'Tcl', 'Erlang', 'Common Lisp', 'scala', 'C', 'Markdown', 'Python', 'Perl', 'php', 'Scheme', 'AWK', 'JavaScript', 'Go', 'julia']
    # langs = ['C#']
    
    for lang in langs:
        file_path = os.path.join(data_path, lang+'.jsonl')
        data = read_jsonl(file_path)
        for line in data:
            if lang == 'AWK': # write ans to txt 
                get_awk_ans(line)         
            path,language_type,task_id=json2file(line)
            print(path)
            if not excute(language_type,path,task_id):
                print('ERROR')
                break 
             
            if lang =='Erlang':
                files_to_delete = glob.glob(os.path.join(beam_path, '*' + "beam"))
                for file_path in files_to_delete:
                    try:
                        os.remove(file_path)
                    except OSError as e:
                        print(f"Error: {e.filename} - {e.strerror}.")   


if __name__ == '__main__':
    valid_label()


