# Copyright (c) Meta Platforms, Inc. and affiliates.

import random
import json
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor
import os
import sys

sys.path.append("..")
from prompts import (
    make_direct_output_prompt,
    make_cot_output_prompt,
    make_direct_input_prompt,
    make_cot_input_prompt,
)

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def extract_answer_direct_output(gen):
    if "==" in gen:
        gen = gen.split("==")[1]
    return gen.strip()

def extract_answer_direct_input(gen):
    if "==" in gen:
        gen = gen.split("==")[0].strip()
    if "assert f" in gen:
        gen = "f" + gen.split("assert f")[1].strip()
    return gen.strip()

def extract_answer_cot_input(gen):
    if "[ANSWER]" in gen:
        gen = gen.split("[ANSWER]")[1].strip()
        if "==" in gen:
            gen = gen.split("==")[0]
        if "assert f" in gen:
            gen = "f" + gen.split("assert f")[1].strip()
        return gen.strip()
    else:
        return gen.split('\n')[-1].strip()

def extract_answer_cot_output(gen):
    if "[ANSWER]" in gen:
        gen = gen.split("[ANSWER]")[1].strip()
        if "==" in gen:
            gen = gen.split("==")[1]
        return gen.strip()
    else:
        return gen.split('\n')[-1].strip()

def call_openai_api(system_prompt, prompt, temperature, n, model, max_tokens, stop) -> list[str]:
    print("not cached")
    prompt = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    while True:
        try:
            result = client.chat.completions.create(
                model=model,
                messages=prompt,
                temperature=temperature,
                n=n,
                max_tokens=max_tokens,
                stop=stop
            )
            break
        except:
            import time; time.sleep(10); pass
    return [result.choices[i].message.content for i in range(n)]

def prompt_openai_general(make_prompt_fn, i, cache, gpt_query, temperature, n, model, max_tokens, stop) -> tuple[str, list[str]]:
    x = random.randint(1, 1000)
    print(f"started {x}")

    full_prompt = make_prompt_fn(gpt_query)
    if temperature == 0:
        cache_key = f"{full_prompt}_{model}"
    else:
        cache_key = f"{full_prompt}_{model}_{str(temperature)}" 

    if cache_key not in cache or (cache_key in cache and n > len(cache[cache_key])):
        cache_result = []
        if cache_key in cache:
            n -= len(cache[cache_key])
            cache_result = cache[cache_key]
        system_prompt = "You are an expert at Python programming, code execution, test case generation, and fuzzing." 
        result = call_openai_api(system_prompt, full_prompt, temperature, n=n, model=model, max_tokens=max_tokens, stop=stop)
        cache[cache_key] = cache_result + result
        print(f"finished {x}")
    else:
        result = cache[cache_key]
        pass
    return i, (cache_key, result)

def batch_prompt(fn, extraction_fn, queries, temperature, n, model, max_tokens, stop):
    # load the cache
    CACHE_DIR_PREFIX = ""
    cache_dir = os.path.join(CACHE_DIR_PREFIX, "cache.json")
    cache_dir_tmp = os.path.join(CACHE_DIR_PREFIX, "cache.json.tmp")
    cache_dir_bak = os.path.join(CACHE_DIR_PREFIX, "cache.json.bak")
    try:
        cache = json.load(open(cache_dir, "r"))
    except:
        json.dump({}, open(cache_dir, "w"))
        cache = {}

    # run the generations
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [
            executor.submit(fn, i, cache, query, temperature, n, model, max_tokens, stop) 
            for i, query in enumerate(queries)
        ]
        results_with_id = [future.result() for future in futures]
    results_with_id.sort()
    results = [i[1] for i in results_with_id]

    # update the cache
    for cache_key, r in results:
        cache[cache_key] = r
    json.dump(cache, open(cache_dir_tmp, "w"))
    os.rename(cache_dir, cache_dir_bak)
    os.rename(cache_dir_tmp, cache_dir)
    os.remove(cache_dir_bak)

    # parse the output
    gens = [i[1] for i in results]
    return [[(extraction_fn(i), i) for i in r] for r in gens]

# direct output prompt
def prompt_direct_output(i, cache, gpt_query, temperature, n, model, max_tokens, stop):
    return prompt_openai_general(make_direct_output_prompt, i, cache, gpt_query, temperature, n, model, max_tokens, stop)

def batch_prompt_direct_output(queries, temperature, n, model, max_tokens, stop):
    return batch_prompt(prompt_direct_output, extract_answer_direct_output, queries, temperature, n, model, max_tokens, stop)

# cot output prompt
def prompt_cot_output(i, cache, gpt_query, temperature, n, model, max_tokens, stop):
    return prompt_openai_general(make_cot_output_prompt, i, cache, gpt_query, temperature, n, model, max_tokens, stop)

def batch_prompt_cot_output(queries, temperature, n, model, max_tokens, stop):
    return batch_prompt(prompt_cot_output, extract_answer_cot_output, queries, temperature, n, model, max_tokens, stop)

# direct input prompt
def prompt_direct_input(i, cache, gpt_query, temperature, n, model, max_tokens, stop):
    return prompt_openai_general(make_direct_input_prompt, i, cache, gpt_query, temperature, n, model, max_tokens, stop)

def batch_prompt_direct_input(queries, temperature, n, model, max_tokens, stop):
    return batch_prompt(prompt_direct_input, extract_answer_direct_input, queries, temperature, n, model, max_tokens, stop)

# cot input prompt
def prompt_cot_input(i, cache, gpt_query, temperature, n, model, max_tokens, stop):
    return prompt_openai_general(make_cot_input_prompt, i, cache, gpt_query, temperature, n, model, max_tokens, stop)

def batch_prompt_cot_input(queries, temperature, n, model, max_tokens, stop):
    return batch_prompt(prompt_cot_input, extract_answer_cot_input, queries, temperature, n, model, max_tokens, stop)