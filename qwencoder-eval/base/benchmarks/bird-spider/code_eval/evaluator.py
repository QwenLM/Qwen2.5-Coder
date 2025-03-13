import inspect
import json
import os
import warnings

from code_eval import tasks
from code_eval.generation import vllm_generation, openai_generation

_WARNING = """
################################################################################
                                  !!!WARNING!!!
################################################################################
The "code_eval"/"apps_metric" you are about to use, execute untrusted 
model-generated code in Python.
Although it is highly unlikely that model-generated code will do something
overtly malicious in response to this test suite, model-generated code may act
destructively due to a lack of model capability or alignment.
Users are strongly encouraged to sandbox this evaluation suite so that it
does not perform destructive actions on their host or network. For more
information on how OpenAI sandboxes its code, see the paper "Evaluating Large
Language Models Trained on Code" (https://arxiv.org/abs/2107.03374).
Once you have read this disclaimer and taken appropriate precautions, set the argument 
"allow_code_execution" to True.
################################################################################\
"""

from vllm import LLM
from transformers import AutoTokenizer
from openai import AsyncOpenAI


class Evaluator:

    def __init__(self, args):

        if args.backend == "vllm":
            self.model = LLM(
                model=args.model,
                max_model_len=8192,
                trust_remote_code=True,
                distributed_executor_backend='ray',
                tensor_parallel_size=int(os.getenv("VLLM_N_GPUS", 1)),
            )
            self.tokenizer = AutoTokenizer.from_pretrained(args.model)
        elif args.backend == "openai":
            self.model = AsyncOpenAI(
                base_url=os.getenv("OPENAI_API_BASE",),
                api_key=os.getenv("OPENAI_API_KEY"),
            )
            self.tokenizer = None
        self.args = args

        # setup arguments
        self.metric_output_path = args.metric_output_path

        # code evaluation permission
        self.allow_code_execution = args.allow_code_execution

    def generate_text(self, task_name):
        task = tasks.get_task(task_name, self.args)
        dataset = task.get_dataset()
        # if args.limit is None, use all samples
        n_tasks = self.args.limit if self.args.limit else len(dataset)
        references = [task.get_reference(dataset[i]) for i in range(self.args.limit_start, self.args.limit_start + n_tasks)]

        if self.args.check_references:
            if "get_solution" in inspect.signature(task.get_reference).parameters:
                solutions = [[task.get_reference(dataset[i], get_solution=True)] for i in range(self.args.limit_start, self.args.limit_start + n_tasks)]
            else:
                solutions = [[ref] for ref in references]
            return solutions, references

        if self.args.backend == "vllm":
            generations = vllm_generation(
                task,
                dataset,
                self.model,
                self.tokenizer,
                n_tasks=n_tasks,
                args=self.args,
            )
        elif self.args.backend == "openai":
            import asyncio
            generations = asyncio.run(openai_generation(
                task,
                dataset,
                self.model,
                self.tokenizer,
                n_tasks=n_tasks,
                args=self.args,
            ),)

        if self.args.do_sample:
            expected_generated = self.args.n_samples
        else:
            expected_generated = self.args.num_beams

        if len(generations[0]) > expected_generated:
            generations = [l[:expected_generated] for l in generations]
            warnings.warn(f"Removing extra predictions from {len(generations[0])} to only keep nsamples={expected_generated}")
        return generations, references

    def evaluate(self, task_name):
        task = tasks.get_task(task_name, self.args)
        if task.requires_execution and not self.allow_code_execution:
            raise ValueError(_WARNING)

        generations, references = self.generate_text(task_name)

        if self.accelerator.is_main_process:
            if not self.args.load_generations_path:
                if self.args.save_generations:
                    with open(self.args.save_generations_path, "w") as fp:
                        generations_line = "\n".join(i[0] for i in generations)
                        json.dump(generations, fp)
                        print(f"generations were saved at {self.args.save_generations_path}")
                if self.args.save_references:
                    with open("references.json", "w") as fp:
                        json.dump(references, fp)
                        print("references were saved at references.json")

            # make sure tokenizer plays nice with multiprocessing
            os.environ["TOKENIZERS_PARALLELISM"] = "false"
            if self.allow_code_execution and task.requires_execution:
                os.environ["HF_ALLOW_CODE_EVAL"] = "1"
            print("Evaluating generations...")
            results = task.process_results(generations, references)
            return results
