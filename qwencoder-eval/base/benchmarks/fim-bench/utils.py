import json
import os
from typing import List, Dict
from transformers import AutoTokenizer

def prepare_prompt(tokenizer, task, model_type, model_name, left_cxt, right_cxt=None, crossfile_cxt=None, args=None):
    if task == "function_completion":
        args.gen_length = 256

    
    # 设置模型特定的tokens
    if "deepseek" in model_name.lower():
        prefix_token = '<｜fim▁begin｜>'
        middle_token = '<｜fim▁end｜>'
        suffix_token = '<｜fim▁hole｜>'
    elif "qwen1.5" in model_name.lower():
        prefix_token = '<fim_prefix>'
        middle_token = '<fim_middle>'
        suffix_token = '<fim_suffix>'
    elif "qwen" in model_name.lower():
        prefix_token = '<|fim_prefix|>'
        middle_token = '<|fim_middle|>'
        suffix_token = '<|fim_suffix|>'
    else:
        prefix_token = '<fim_prefix>'
        middle_token = '<fim_middle>'
        suffix_token = '<fim_suffix>'
        
    if model_type == "codelm_leftright_context":
        left_cxt_truncated = tokenizer.decode(tokenizer.encode(left_cxt)[-(args.max_seq_length - args.gen_length - args.right_context_length):])
        right_cxt_truncated = tokenizer.decode(tokenizer.encode(right_cxt)[:args.right_context_length])
        prompt = f'{prefix_token}{left_cxt_truncated}{suffix_token}{right_cxt_truncated}{middle_token}'
    elif model_type == "codelm_right_cfc_left":
        assert crossfile_cxt is not None
        left_cxt_truncated = tokenizer.decode(tokenizer.encode(left_cxt)[-(args.max_seq_length - args.gen_length - args.right_context_length - args.cfc_seq_length):])
        right_cxt_truncated = tokenizer.decode(tokenizer.encode(right_cxt)[:args.right_context_length])
        crossfile_cxt_truncated = tokenizer.decode(tokenizer.encode('\n\n' + crossfile_cxt)[:args.cfc_seq_length])
        prompt = f'{prefix_token}{left_cxt_truncated}{suffix_token}{right_cxt_truncated}{crossfile_cxt_truncated}{middle_token}'
    else:
        raise NotImplementedError
    return prompt

