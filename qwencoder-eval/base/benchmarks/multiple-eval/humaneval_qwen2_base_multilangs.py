import json
import os
from pathlib import Path

from human_eval.evaluation import evaluate_functional_correctness
from tqdm import tqdm
from utils.dataset import HumanEvalDataset
from utils.utils import cleanup_code
from vllm import LLM, SamplingParams

COMMON_EOS = [
    "<|endoftext|>",
    "<|endofmask|>",
    "</s>",
]


class HumanEval:
    """
    HumanEval evaluation class.
    """

    def __init__(
        self,
        data_root,
        max_seq_len=2048,
        language="python",
        max_gen_len=200,
        log_dir=None,
        temperature=0,
        top_p=0.95,
        n_sample=40,
        k_sample=1,
        no_batching=False,
        no_new_line_at_last=False,
    ):
        self.data_root = data_root
        self.max_seq_len = max_seq_len
        self.max_gen_len = max_gen_len
        self.k = k_sample
        self.n_sample = n_sample
        self.log_dir = log_dir
        self.temperature = temperature
        self.top_p = top_p
        self.sft = False
        self.no_batching = no_batching
        self.no_new_line_at_last = no_new_line_at_last

        self.eos = COMMON_EOS
        print(f"EOS: {self.eos}")

        os.makedirs(self.log_dir, exist_ok=True)

    def eval_model_multiple(self, llm, langs, just_eval=False):
        print(f"To test: {langs}")

        if not just_eval:
            for lang in langs:
                print(f">>> Inference: {lang}")
                self.eval_model(llm, lang)
        else:
            print(f"Skip generation, just eval...")

        metric = {}
        for lang in langs:
            print(f">> Testing: {lang}")
            metric.update(self._calculate_final_score(lang))

        return metric

    def eval_model(self, llm: LLM, lang_name: str):
        assert self.log_dir is not None, "log_dir should not be None when evaluating humaneval"
        dataset = HumanEvalDataset(self.data_root, sample_num=self.n_sample, language=lang_name, issft=self.sft)
        if self.k > 1:
            assert self.n_sample >= 100, "HumanEval PASS@100 needs n_sample >= 100"

        sampling_params = SamplingParams(max_tokens=self.max_gen_len, temperature=self.temperature, top_p=self.top_p, stop=self.eos)

        # Generate.
        with Path(self.log_file_path(lang_name)).open("w") as f_log:
            print(f"{self.no_new_line_at_last = }")
            if not self.no_new_line_at_last:  # qwen +\n
                prompts = [data["prompt"] + "\n" for data in dataset]
            else:  # no_new_line_at_last, strip it
                prompts = [data["prompt"].strip() for data in dataset]

            if self.no_batching:
                print(f"Disable: continuous batching. This will be slow.")
                generated = [llm.generate(prompt, sampling_params, use_tqdm=False)[0] for prompt in tqdm(prompts)]
            else:
                print(f"Enable: continuous batching.")
                generated = llm.generate(prompts, sampling_params, use_tqdm=True)

            for idx, output in enumerate(generated):
                data = dataset[idx]
                # suffixprediction = output.outputs[0].text.replace("\t", "    ")
                suffixprediction = output.outputs[0].text
                prediction = output.prompt + suffixprediction
                suffixprediction = cleanup_code(suffixprediction, lang_name, "humaneval", self.sft, dataset.stopwords)
                original_prompt = data["original_prompt"]
                if not self.sft:
                    suffixprediction = original_prompt + "\n" + suffixprediction
                res = {
                    "task_id": data["task_id"],
                    "generation": suffixprediction,
                    "prompt": original_prompt,
                    "wholecode": prediction,
                }
                f_log.write(json.dumps(res, ensure_ascii=False) + "\n")

    def log_file_path(self, lang_name) -> str:
        return os.path.join(self.log_dir, f"pred_{lang_name}_output.jsonl")

    def _calculate_final_score(self, lang_name):
        timeout = 10
        res, details = evaluate_functional_correctness(
            input_file=self.log_file_path(lang_name),
            problem_file=os.path.join(self.data_root, f"humaneval-{lang_name}.jsonl"),
            tmp_dir=self.log_dir,
            timeout=timeout,
            language=lang_name,
        )
        res = res["pass@%d" % self.k]
        print(f"{lang_name} score is", res)

        details_file = os.path.join(self.log_dir, f"humaneval-{lang_name}-details.json")
        with Path(details_file).open("w") as f:
            json.dump(details, f, ensure_ascii=False, indent=2)

        print(f"Details => {details_file}")
        return {lang_name: round(100 * res, 2)}
