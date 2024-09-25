from data import get_bigcodebench, write_jsonl

subset = 'hard'
split = 'complete'
dataset = get_bigcodebench(subset=subset)

task = f'bigcodebench/bcb_{split}_{subset}'
outputs = []
for key, value in dataset.items():
    outputs.append({
        'task_id': value['task_id'],
        'prompt': value['complete_prompt'] if split == 'complete' else value['instruct_prompt'],
        'complete_prompt': value['complete_prompt'],
        'instruct_prompt': value['instruct_prompt'],
        'canonical_solution': value['canonical_solution'],
        'code_prompt': value['code_prompt'],
        'test': value['test'],
        'entry_point': value['entry_point'],
        'doc_struct': value['doc_struct'],
        'libs': value['libs'],
        'task': task,
    })

save_path = f'{task}.jsonl'
write_jsonl(save_path, outputs)
