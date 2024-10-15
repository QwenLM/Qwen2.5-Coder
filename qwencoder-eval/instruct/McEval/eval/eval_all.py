from json2file import read_jsonl, json2file
from save2file import save2file,save2file_with_tempdir
from excute import excute
from extract import extract
import json
import os 
import argparse
from excute import get_awk_ans
import glob
import traceback
import tempfile
import shutil
import random 

def prepare_tempdir_context(temp_dir):
    shutil.copytree('../data/AWK', os.path.join(temp_dir, 'data/AWK'),dirs_exist_ok=True)
    shutil.copytree('../data/C#', os.path.join(temp_dir, 'C#'),dirs_exist_ok=True)
    shutil.copytree('../data/Common Lisp', os.path.join(temp_dir, 'Common Lisp'),dirs_exist_ok=True)
    shutil.copytree('../data/F#', os.path.join(temp_dir, 'F#'),dirs_exist_ok=True)
    shutil.copytree('../data/rust', os.path.join(temp_dir, 'rust'),dirs_exist_ok=True)
    shutil.copytree('../data/go', os.path.join(temp_dir, 'go'),dirs_exist_ok=True)
    shutil.copytree('../data/HTML', os.path.join(temp_dir, 'HTML'),dirs_exist_ok=True)
    shutil.copytree('../data/JSON', os.path.join(temp_dir, 'JSON'),dirs_exist_ok=True)
    shutil.copytree('../data/Markdown', os.path.join(temp_dir, 'Markdown'),dirs_exist_ok=True)
    shutil.copytree('../data/Visual Basic', os.path.join(temp_dir, 'Visual Basic'),dirs_exist_ok=True)
    
def calculate_accuracy(args, lang, temp_dir):
    items = [json.loads(x) for x in open(f"{args.result_path}/{lang}.jsonl").readlines() if x]
    correct_count = 0
    fim_result = {'single': {"correct": 0, "accuracy": 0, 'total_count': 0}, 
                  'multi' : {"correct": 0, "accuracy": 0, 'total_count': 0}, 
                  'span'  : {"correct": 0, "accuracy": 0, 'total_count': 0} }

    detail_scores = []  

    for item in items:
        if lang == 'AWK':
            get_awk_ans(item, temp_dir)
        try:
            code = extract(item["raw_generation"][0], item, lang)
        except:
            print(f'+++++ Extract {item["task_id"]} failed')
            code = "1234"  #avoid code file is empty    
        if code is None:
            code = "1234"

        path, _, _ = save2file_with_tempdir(content=code, language_type=lang, item=item, temp_dir=temp_dir)

        if 'single' in item['task_id']:
            fim_result['single']['total_count']+=1
        elif 'multi' in item['task_id']:
            fim_result['multi']['total_count']+=1
        elif 'span' in item['task_id']:
            fim_result['span']['total_count']+=1
        # try:
        if excute(lang, path, item["task_id"], temp_dir=temp_dir):
            correct_count += 1
            if 'single' in item['task_id']:
                fim_result['single']['correct']+=1
            elif 'multi' in item['task_id']:
                fim_result['multi']['correct']+=1
            elif 'span' in item['task_id']:
                fim_result['span']['correct']+=1
        # except:
        #     traceback.print_exc()
            detail_scores.append({'task_id':item['task_id'], 'pass':True })
        else:
            detail_scores.append({'task_id':item['task_id'], 'pass':False})

    accuracy = correct_count / len(items)
    if fim_result['single']['total_count']:
        fim_result['single']['accuracy'] = fim_result['single']['correct']/fim_result['single']['total_count']
    if fim_result['multi']['total_count']:
        fim_result['multi']['accuracy'] = fim_result['multi']['correct']/fim_result['multi']['total_count']
    if fim_result['span']['total_count']:
        fim_result['span']['accuracy'] = fim_result['span']['correct']/fim_result['span']['total_count']  

           
    return {"correct": correct_count, "accuracy": accuracy, 'total_count': len(items), 'fim_result':fim_result},  detail_scores 


def clean_cache():
    beam_path = '/workspace/MMCodeEval/eval'
    files_to_delete = glob.glob(os.path.join(beam_path, '*' + "beam"))
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
        except OSError as e:
            print(f"Error: {e.filename} - {e.strerror}.")

    go_cache_path ='/workspace/MMCodeEval/data/go'
    files_to_delete = glob.glob(os.path.join(go_cache_path, '*' + ".go"))
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
        except OSError as e:
            print(f"Error: {e.filename} - {e.strerror}.")

    tmp_cache_path ='/workspace/MMCodeEval/eval/tmp'
    files_to_delete = glob.glob(os.path.join(tmp_cache_path, '*'))
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
        except OSError as e:
            print(f"Error: {e.filename} - {e.strerror}.")

def eval(args):
    clean_cache()
    exclude_langs = ['sql']

    langs = [x.split('.')[0] for x in os.listdir(args.result_path) if x.endswith('.jsonl')]
    save_path = os.path.join(args.save_path, os.path.basename(args.result_path)+'.jsonl')
    detail_save_path = os.path.join(args.save_path, os.path.basename(args.result_path)+'_detail.jsonl')
    # print(save_path)
    if os.path.exists(save_path):
        finish_langs = [x.split('\t')[0].strip().lower() for x in open(save_path, 'r').readlines()]
    else:
        finish_langs = []
  
    langs = [lang for lang in langs if (lang.lower() not in exclude_langs+finish_langs)]
    random.shuffle(langs)

    print(langs)
    score = {}
    
    # with tempfile.TemporaryDirectory() as temp_dir:
    temp_dir = '/workspace/MMCodeEval/eval/tmp'
    prepare_tempdir_context(temp_dir)
    # orgin_dir = os.getcwd()
    os.chdir(temp_dir)
    for lang in langs:
        lang_score, detail_scores = calculate_accuracy(args, lang, temp_dir)
        score[lang] = lang_score 
        print('#'*80)
        print('#'*80)
        print('\n'*3)
        print(f'Lang: {lang}')
        print(score[lang])

        with open(save_path, 'a') as f:
            f.write(lang+'\t'+json.dumps(score[lang])+'\n')

        # with open(detail_save_path, 'a') as f:
        #     f.write(lang+'\t'+json.dumps(detail_scores)+'\n')
        
        print('\n'*3)
        print('#'*80)
        print('#'*80)
        # clean_cache()
    print(score)


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--result_path', type=str, default='/workspace/MMCodeEval/result/process_result_0313/split_result/outputs_fim_light/deepseek-coder-7b-instruct')
    arg_parser.add_argument('--save_path', type=str, default='/workspace/MMCodeEval/result/process_result_0313/fim_light')
    args = arg_parser.parse_args()
    eval(args)
    