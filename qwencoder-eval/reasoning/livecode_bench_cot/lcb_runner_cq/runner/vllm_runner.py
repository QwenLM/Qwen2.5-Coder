try:
    from vllm import LLM, SamplingParams
except ImportError:
    print("Cannot import vllm")

from lcb_runner_cq.runner.base_runner import BaseRunner
import time
import random


class VLLMRunner(BaseRunner):
    def __init__(self, args, model):
        super().__init__(args, model)

        self.llm = LLM(
            model.model_name,
            tensor_parallel_size=args.tensor_parallel_size,
            dtype=args.dtype,
            enforce_eager=True,
            gpu_memory_utilization=0.98,
            distributed_executor_backend="ray",
            trust_remote_code=True,
        )
        print(f"Loading from {model.model_name}")
        self.sampling_params = SamplingParams(
            n=self.args.n,
            max_tokens=self.args.max_tokens,
            stop=self.args.stop,
            # ------------------------
            temperature=self.args.temperature,
            top_p=self.args.top_p,
            top_k=self.args.top_k,
            repetition_penalty=self.args.rp,
            seed=self.args.seed,
        )
        print(f"{self.sampling_params = }")

    def _run_single(self, prompt: str) -> list[str]:
        outputs = self.llm.generate([prompt], self.sampling_params)
        return [o.text for o in outputs[0].output.outputs]

    # def run_batch(self, prompts: list[str]) -> list[list[str]]:
    #     print("vllm.run_batch")
    #     print("=*" * 120)
    #     print(prompts[0])
    #     outputs = self.llm.generate(prompts, self.sampling_params)
    #     ret = []
    #     for output in outputs:
    #         ret.append([o.text for o in output.outputs])
    #     return ret

    def run_batch(self, prompts: list[str]) -> list[list[str]]:
        print("vllm.run_batch")
        print(f"{self.sampling_params = }")
        print("=*" * 120)
        print(prompts[0])

        # chunk_size_max = 128
        chunk_size_max = 256
        chunk_size = max(chunk_size_max // self.args.n, 1)

        print(f" - {chunk_size_max = }")
        print(f" - {self.args.n = }")
        print(f" - Therefore: {chunk_size = }")

        ret = []
        for chunk_num, i in enumerate(range(0, len(prompts), chunk_size)):
            chunk = prompts[i : i + chunk_size]
            print(f"Processing chunk {chunk_num + 1} with {len(chunk)} prompts")

            outputs = self.llm.generate(chunk, self.sampling_params)
            for output in outputs:
                ret.append([o.text for o in output.outputs])

        return ret

    def run_one_by_one(self, prompts: list[str]) -> list[list[str]]:
        print("vllm.run_one_by_one")
        print("=*" * 120)
        print(prompts[0])

        ret = []
        for idx, prompt in enumerate(prompts):
            tic = time.time()
            print(f"Start {idx=}")
            output = self.llm.generate([prompt], self.sampling_params, use_tqdm=True)[0]
            toc = time.time()
            ret.append([o.text for o in output.outputs])
            print(f"Sample-{idx:04d} @ {toc-tic:.2f}s")
            if idx == 0:
                print("<<<<")
                print(output.outputs[0].text)
                print(">>>>")

        return ret
