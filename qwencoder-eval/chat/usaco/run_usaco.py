'''
Contains all code to duplicate experiments in "Can language models solve olympiad programming questions?"
To utilize open models, create your own callable model function in models.py, and import it as with GPTs/Claude.
'''

import argparse
from functools import partial
from models import gpts, claude
from USACOBench.prompts import RetrievalType
from USACOBench.data_utils import load_problem_dict
from USACOBench.evaluation import print_metrics
from dotenv import load_dotenv
from utils import run_solve, run_retrieval, run_reflexion, calculate_final_rs
from collections import Counter

load_dotenv()

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--model_name', help='model endpoint: ie. gpt-4-1106-preview', default='gpt-3.5-turbo')
parser.add_argument('-e', '--episodic_retrieval', help='whether to use episodic retrieval', action="store_true", default=False)
parser.add_argument('-f', '--num_retrieved', help='number of documents retrieved', default=2)
parser.add_argument('-s', '--semantic_retrieval', help='whether to use semantic retrieval', action="store_true", default=False)
parser.add_argument('-r', '--reflexion', help='whether to use reflexion', action="store_true", default=False)
parser.add_argument('-a', '--attempts', help='number of attempts', type=int, default=1)
parser.add_argument('-n', '--num_reflexion', help='number of reflexion iterations', default=2)
parser.add_argument('-o', '--outputs_dir', help='output directory', default='/tmp/usaco/results')
args = parser.parse_args()

print('Running with the following arguments:')
print(args)

model_name = args.model_name
if 'gpt' in model_name or 'openai' in model_name:
    model_fn = gpts
elif 'claude' in model_name:
    model_fn = claude
else:
    raise Exception("Model name not one of gpt or claude. Please modify code to add model support.")

problem_dict = load_problem_dict('usaco_subset307')
model_fn = partial(model_fn, model=model_name)

# A little redundant but it does the job and it's readable...
if not args.episodic_retrieval and not args.semantic_retrieval and not args.reflexion:
    rdict, sdict, rs, ss = run_solve(model_fn, model_name, problem_dict, args.attempts, args.outputs_dir)

elif args.episodic_retrieval and not args.semantic_retrieval and not args.reflexion:
    rdict, sdict, rs, ss = run_solve(model_fn, model_name, problem_dict, args.attempts)
    rdict, sdict, rs, ss = run_retrieval(model_fn, model_name, problem_dict, args.attempts, ss, args.num_retrieved, RetrievalType.EPISODIC, args.outputs_dir)

elif not args.episodic_retrieval and args.semantic_retrieval and not args.reflexion:
    rdict, sdict, rs, ss = run_solve(model_fn, model_name, problem_dict, args.attempts)
    rdict, sdict, rs, ss = run_retrieval(model_fn, model_name, problem_dict, args.attempts, ss, args.num_retrieved, RetrievalType.SEMANTIC, args.outputs_dir)

elif args.episodic_retrieval and args.semantic_retrieval and not args.reflexion:
    rdict, sdict, rs, ss = run_solve(model_fn, model_name, problem_dict, args.attempts)
    rdict, sdict, rs, ss = run_retrieval(model_fn, model_name, problem_dict, args.attempts, ss, args.num_retrieved, RetrievalType.EPISODIC_SEMANTIC, args.outputs_dir)

elif not args.episodic_retrieval and not args.semantic_retrieval and args.reflexion:
    rdict, sdict, rs, ss = run_solve(model_fn, model_name, problem_dict, args.attempts)
    reflexions = [rdict]
    query_dict = None
    for i in range(args.num_reflexion):
        rdict, sdict, rs, ss, query_dict = run_reflexion(model_fn, model_name, problem_dict, args.attempts, rdict, sdict, query_dict, i, return_queries=True)
        reflexions.append(rdict)

    rs = calculate_final_rs(reflexions, problem_dict)

elif args.episodic_retrieval and not args.semantic_retrieval and args.reflexion:
    rdict, sdict, rs, ss = run_solve(model_fn, model_name, problem_dict, args.attempts)
    rdict, sdict, rs, ss = run_retrieval(model_fn, model_name, problem_dict, args.attempts, ss, args.num_retrieved, RetrievalType.EPISODIC, args.outputs_dir)

    reflexions = [rdict]
    query_dict = None
    for i in range(args.num_reflexion):
        rdict, sdict, rs, ss, query_dict = run_reflexion(model_fn, model_name, problem_dict, args.attempts, rdict, sdict, query_dict, i, return_queries=True, retrieval=True)
        reflexions.append(rdict)

    rs = calculate_final_rs(reflexions, problem_dict)

elif not args.episodic_retrieval and args.semantic_retrieval and args.reflexion:
    rdict, sdict, rs, ss = run_solve(model_fn, model_name, problem_dict, args.attempts)
    rdict, sdict, rs, ss = run_retrieval(model_fn, model_name, problem_dict, args.attempts, ss, args.num_retrieved, RetrievalType.SEMANTIC, args.outputs_dir)

    reflexions = [rdict]
    query_dict = None
    for i in range(args.num_reflexion):
        rdict, sdict, rs, ss, query_dict = run_reflexion(model_fn, model_name, problem_dict, args.attempts, rdict, sdict, query_dict, i, return_queries=True, retrieval=True)
        reflexions.append(rdict)

    rs = calculate_final_rs(reflexions, problem_dict)

elif args.episodic_retrieval and args.semantic_retrieval and args.reflexion:
    rdict, sdict, rs, ss = run_solve(model_fn, model_name, problem_dict, args.attempts)
    rdict, sdict, rs, ss = run_retrieval(model_fn, model_name, problem_dict, args.attempts, ss, args.num_retrieved, RetrievalType.EPISODIC_SEMANTIC, args.outputs_dir)

    reflexions = [rdict]
    query_dict = None
    for i in range(args.num_reflexion):
        rdict, sdict, rs, ss, query_dict = run_reflexion(model_fn, model_name, problem_dict, args.attempts, rdict, sdict, query_dict, i, return_queries=True, retrieval=True)
        reflexions.append(rdict)

    rs = calculate_final_rs(reflexions, problem_dict)

print_metrics(rs)
print('Result summary:')
result_types = [result['result_type'] for result_set in rs for result in result_set]
print(Counter(result_types))
print()
