import pathlib

from lcb_runner.lm_styles import LanguageModel, LMStyle
from lcb_runner.utils.scenarios import Scenario


def ensure_dir(path: str, is_file=True):
    if is_file:
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    else:
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    return


def get_cache_path(model: LanguageModel, args) -> str:
    model_repr = model.model_repr
    scenario = args.scenario
    n = args.n
    temperature = args.temperature
    path = f"cache/{model_repr}/{scenario}_{n}_{temperature}.json"
    ensure_dir(path)
    return path


def get_output_path(model: LanguageModel, args) -> str:
    model_repr = model.model_repr
    scenario = args.scenario
    n = args.n
    temperature = args.temperature
    path = f"output/{model_repr}/{scenario}_{n}_{temperature}.json"
    ensure_dir(path)
    return path


def get_eval_all_output_path(model: LanguageModel, args) -> str:
    model_repr = model.model_repr
    scenario = args.scenario
    n = args.n
    temperature = args.temperature
    path = f"output/{model_repr}/{scenario}_{n}_{temperature}_eval_all.json"
    return path
