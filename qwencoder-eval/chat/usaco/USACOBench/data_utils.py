import pandas as pd
import datasets
import random
import json
from typing import List, Dict, Any, Union

Problem = Dict[Any, Any]

DATASET_PATH = 'data/datasets/{}'
DICT_PATH = 'data/datasets/{}_dict.json'
CORPUS_PATH = 'data/corpuses/{}.json'
SEED = 123
random.seed(SEED)

# TODO finish save problems, add verbose

# TODO check if datasets.Dataset registers as List[Problem] in typing
def load_problems(dataset: str,
                  load_from_disk=True,
                  num_problems: Union[int, None] = None,
                  dataset_path: str = DATASET_PATH) -> datasets.Dataset:
    '''
    Loads datasets.Dataset of problems
    if load_from_disk == True, we load locally,
        otherwise we load from HuggingFace cloud
    num_problems: randomly samples this number of problems without
        replacement, or returns entire dataset if None
    '''
    dataset_loc = dataset_path.format(dataset)
    if load_from_disk:
        dataset = datasets.load_from_disk(dataset_loc)
    else:
        dataset = datasets.load_dataset(dataset_loc)
    if num_problems is None:
        return dataset
    return sample_from_dataset(dataset, num_problems)

def save_problems(problems,
                  dataset: str,
                  save_to_disk=True,
                  dataset_path: str = DATASET_PATH,
                  convert_from_list=True,
                  verbose=True):
    '''
    Saves datasets.Dataset of problems
    convert_from_list: input is a list of dicts, we want to save as datasets.Dataset
    '''
    assert save_to_disk is True, 'Only local saving is supported'
    dataset_loc = dataset_path.format(dataset)
    if verbose:
        print('Saving to', dataset_loc)
    if convert_from_list:
        problems = datasets.Dataset.from_pandas(pd.DataFrame(problems))
        problems.save_to_disk(dataset_loc)

def load_problem_dict(dataset: str,
                      dict_path: str = DICT_PATH) -> Dict[str, Problem]:
    '''
    Loads (problem_id, Problem) dictionary of problems
    '''
    with open(dict_path.format(dataset), 'r') as f:
        return json.load(f)

def save_problem_dict(problem_dict: Dict[str, Problem],
                      dataset: str,
                      dict_path: str = DICT_PATH,
                      verbose=True):
    '''
    Saves (problem_id, Problem) dictionary of problems
    '''
    dict_loc = dict_path.format(dataset)
    print('Saving to', dict_loc)
    with open(dict_loc, 'w') as f:
        json.dump(problem_dict, f)

def load_corpus(corpus: str,
                corpus_path: str = CORPUS_PATH) -> List[str]:
    '''
    Loads corpus (list of strings)
    '''
    with open(corpus_path.format(corpus), 'r') as f:
        return json.load(f)

def save_corpus(docs: List[str],
                corpus: str,
                corpus_path: str = CORPUS_PATH,
                verbose=True):
    '''
    Saves corpus (list of strings)
    '''
    corpus_loc = corpus_path.format(corpus)
    print('Saving to', corpus_loc)
    with open(corpus_loc, 'w') as f:
        json.dump(docs, f)

def sample_from_dataset(dataset: datasets.Dataset,
                         num_samples) -> datasets.Dataset:
    assert num_samples <= len(dataset), 'num samples {} is more than length of dataset {}'.format(num_samples, len(dataset))
    return dataset.select(random.sample(range(len(dataset)), num_samples))
