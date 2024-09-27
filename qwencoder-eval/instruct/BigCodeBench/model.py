import json
import os
from abc import ABC, abstractmethod
from typing import List
from warnings import warn

import openai

try:
    import anthropic

    from bigcodebench.gen.util import anthropic_request
except ImportError:
    warn("Anthropic decoder will not work. Fix by `pip install anthropic`")

# mistral.ai
try:
    from mistralai.client import MistralClient
    from mistralai.models.chat_completion import ChatMessage
except ImportError:
    warn("MistralAI decoder will not work. Fix by `pip install mistralai`")
try:
    import google.generativeai as genai
except ImportError:
    warn("GoogleGenAI decoder will not work. Fix by `pip install google-generativeai`")

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

try:
    from vllm import LLM, SamplingParams
except ImportError:
    warn("VLLM decoder will not work. Fix by `pip install vllm`")

from gen.util import openai_request

EOS = [
    "<|endoftext|>",
    "<|endofmask|>",
    "</s>",
    "\nif __name__",
    "\ndef main(",
    "\nprint(",
]


def extra_eos_for_direct_completion(dataset) -> List[str]:
    if dataset.lower() == "bigcodebench":
        return ["\ndef ", "\nclass ", "\nimport ", "\nfrom ", "\nassert "]
    raise ValueError(f"Unknown dataset: {dataset}")


# some random words which serves as the splitter
_MAGIC_SPLITTER_ = "-[[]]-this-is-really-our-highest-priority-[[]]-"


def make_chat_prompt(prompt: str, tokenizer: AutoTokenizer) -> str:
    # directly return prompt if it does not have a tokenizer.chat_template
    if tokenizer.chat_template is None:
        return prompt

    prompt = f"""\
Please provide a self-contained Python script that solves the following problem in a markdown code block:
```
{prompt.strip()}
```
"""
    response = f"""\
Below is a Python script with a self-contained function that solves the problem and passes corresponding tests:
```python
{_MAGIC_SPLITTER_}
```
"""
    prompt = tokenizer.apply_chat_template(
        [
            {
                "role": "user",
                "content": prompt
            },
            {
                "role": "assistant",
                "content": response
            },
        ],
        tokenize=False,
    ).split(_MAGIC_SPLITTER_)[0]
    return prompt


class DecoderBase(ABC):

    def __init__(
        self,
        name: str,
        batch_size: int = 1,
        temperature: float = 0.8,
        max_new_tokens: int = 1280,
        dtype: str = "bfloat16",  # default
        trust_remote_code: bool = False,
        tokenizer_name: str = None,
        tokenizer_legacy: bool = False,
    ) -> None:
        print("Initializing a decoder model: {} ...".format(name))
        self.name = name
        self.batch_size = batch_size
        self.temperature = temperature
        self.eos = EOS
        self.skip_special_tokens = False
        self.max_new_tokens = max_new_tokens
        self.dtype = dtype
        self.trust_remote_code = trust_remote_code
        self.tokenizer_name = tokenizer_name
        self.tokenizer_legacy = tokenizer_legacy

    @abstractmethod
    def codegen(self, prompt: str, do_sample: bool = True, num_samples: int = 200) -> List[str]:
        pass

    @abstractmethod
    def is_direct_completion(self) -> bool:
        pass

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name


class VllmDecoder(DecoderBase):

    def __init__(self, name: str, dataset: str, tp: int, **kwargs) -> None:
        super().__init__(name, **kwargs)

        kwargs = {
            "tensor_parallel_size": int(os.getenv("VLLM_N_GPUS", tp)),
            "dtype": self.dtype,
            "trust_remote_code": True,
            "enforce_eager": True,
            "gpu_memory_utilization": 0.95,
            "worker_use_ray": True
        }
        if self.tokenizer_name is None:
            self.tokenizer_name = self.name

        self.tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_name, **kwargs, legacy=self.tokenizer_legacy)
        if self.tokenizer.chat_template is None:
            self.eos += extra_eos_for_direct_completion(dataset)
        self.llm = LLM(model=name, max_model_len=2048, **kwargs)
        self.llm.set_tokenizer(tokenizer=self.tokenizer)

    def is_direct_completion(self) -> bool:
        return self.tokenizer.chat_template is None

    def codegen(self, prompts: List[str], do_sample: bool = True, num_samples: int = 200) -> List[str]:
        if do_sample:
            assert self.temperature > 0, "Temperature must be greater than 0!"

        vllm_outputs = self.llm.generate(
            prompts,
            SamplingParams(
                temperature=self.temperature,
                max_tokens=self.max_new_tokens,
                top_p=0.95 if do_sample else 1.0,
                stop=self.eos,
            ),
            use_tqdm=True,
        )

        gen_strs = [x.outputs[0].text.replace("\t", "    ") for x in vllm_outputs]
        return gen_strs


class GeneralVllmDecoder(VllmDecoder):

    def __init__(self, name: str, **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.eos += ["\n```\n"]
        print(f"EOS strings: {self.eos}")

    def codegen(self, prompts: List[str], do_sample: bool = True, num_samples: int = 200) -> List[str]:
        chat_prompts = [make_chat_prompt(prompt, self.tokenizer) for prompt in prompts]
        return VllmDecoder.codegen(self, chat_prompts, do_sample, num_samples)


class HfTorchDecoder(DecoderBase):

    def __init__(self, name: str, dataset: str, **kwargs):
        super().__init__(name=name, **kwargs)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        kwargs = {}
        kwargs["device_map"] = "auto"
        kwargs["trust_remote_code"] = self.trust_remote_code
        # string to torch dtype
        kwargs["torch_dtype"] = getattr(torch, self.dtype)
        self.skip_special_tokens = True

        print(f"{kwargs = }", self.tokenizer_name)
        if self.tokenizer_name is None:
            self.tokenizer_name = self.name

        self.tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_name, **kwargs, legacy=self.tokenizer_legacy)

        if self.tokenizer.chat_template is None:
            self.eos += extra_eos_for_direct_completion(dataset)

        self.model = AutoModelForCausalLM.from_pretrained(name, **kwargs)
        self.model = self.model.to(self.device)

    def is_direct_completion(self) -> bool:
        return self.tokenizer.chat_template is None

    @torch.inference_mode()
    def codegen(self, prompt: str, do_sample: bool = True, num_samples: int = 200) -> List[str]:
        if self.temperature == 0:
            assert not do_sample
            assert num_samples == 1

        input_tokens = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)
        kwargs = {}
        if do_sample:
            kwargs["top_p"] = 0.95
            kwargs["temperature"] = self.temperature

        outputs = self.model.generate(
            input_tokens,
            max_new_tokens=self.max_new_tokens,
            do_sample=do_sample,
            num_return_sequences=min(self.batch_size, num_samples),
            pad_token_id=self.tokenizer.eos_token_id,
            stop_strings=self.eos,
            tokenizer=self.tokenizer,
            **kwargs,
        )

        gen_strs = self.tokenizer.batch_decode(
            outputs[:, input_tokens.size(-1):],
            skip_special_tokens=self.skip_special_tokens,
        )
        outputs = []
        # removes eos tokens.
        for output in gen_strs:
            min_index = 10000
            for eos in self.eos:
                if eos in output:
                    min_index = min(min_index, output.index(eos))
            outputs.append(output[:min_index].replace("\t", "    "))
        return outputs


class GenenralHfTorchDecoder(HfTorchDecoder):

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, **kwargs)
        self.eos += ["\n```\n"]
        print(f"EOS strings: {self.eos}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_name if self.tokenizer_name else self.name, **kwargs, legacy=self.tokenizer_legacy)

    def codegen(self, prompt: str, do_sample: bool = True, num_samples: int = 200) -> List[str]:
        prompt = make_chat_prompt(prompt, self.tokenizer)
        return HfTorchDecoder.codegen(self, prompt, do_sample, num_samples)


class OpenAIChatDecoder(DecoderBase):

    def __init__(self, name: str, base_url=None, **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.client = openai.OpenAI(base_url=base_url)

    def codegen(self, prompt: str, do_sample: bool = True, num_samples: int = 200) -> List[str]:
        if do_sample:
            assert self.temperature > 0, "Temperature must be positive for sampling"
        batch_size = min(self.batch_size, num_samples)

        # construct prompt
        fmt = "json_object" if self.name == "gpt-4-1106-preview" else "text"
        if fmt == "json_object":
            message = r'Please complete the following code snippet by generating JSON like {"code": ""}'
        else:
            message = r"Please generate self-contained code to complete the following problem:"

        message += f"\n```python\n{prompt.strip()}\n```"

        ret = openai_request.make_auto_request(
            self.client,
            message=message,
            model=self.name,
            max_tokens=self.max_new_tokens,
            temperature=self.temperature,
            n=batch_size,
            response_format={"type": fmt},
        )

        outputs = []
        for item in ret.choices:
            content = item.message.content
            # if json serializable
            if fmt == "json_object":
                try:
                    json_data = json.loads(content)
                    if json_data.get("code", None) is not None:
                        outputs.append(prompt + "\n" + json_data["code"])
                        continue

                    print(f"'code' field not found in: {json_data}")
                except Exception as e:
                    print(e)
            outputs.append(content)

        return outputs

    def is_direct_completion(self) -> bool:
        return False


class MistralChatDecoder(DecoderBase):

    def __init__(self, name: str, **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.client = MistralClient(api_key=os.getenv("MISTRAL_API_KEY"))

    def codegen(self, prompt: str, do_sample: bool = True, num_samples: int = 200) -> List[str]:
        kwargs = {}
        if do_sample:
            assert self.temperature > 0, "Temperature must be positive for sampling"
            kwargs["top_p"] = 0.95
            kwargs["temperature"] = self.temperature
        else:
            self.temperature = 0

        batch_size = min(self.batch_size, num_samples)

        outputs = []
        for _ in range(batch_size):
            ret = self.client.chat(
                model=self.name,
                messages=[ChatMessage(
                    role="user",
                    content="Please generate self-contained code to solve the following problem in a Python markdown block:" + f"\n```python\n{prompt.strip()}\n```",
                )],
                max_tokens=self.max_new_tokens,
                **kwargs,
            )

            outputs.append(ret.choices[0].message.content)

        return outputs

    def is_direct_completion(self) -> bool:
        return False


class AnthropicDecoder(DecoderBase, ABC):
    def __init__(self, name: str, **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_KEY"))

    def is_direct_completion(self) -> bool:
        return False


class AnthropicMessageDecoder(AnthropicDecoder):

    def codegen(self, prompt: str, do_sample: bool = True, num_samples: int = 200) -> List[str]:
        kwargs = {}
        if do_sample:
            assert self.temperature > 0, "Temperature must be positive for sampling"
            kwargs["top_p"] = 0.95
            kwargs["temperature"] = self.temperature
        else:
            self.temperature = 0

        batch_size = min(self.batch_size, num_samples)
        if not do_sample:
            assert batch_size == 1, "Sampling only supports batch size of 1"

        outputs = []
        for _ in range(batch_size):
            message = anthropic_request.make_auto_request(
                client=self.client,
                model=self.name,
                messages=[{
                    "role": "user",
                    "content": "Please generate self-contained code to complete the following problem wrapped in a Python markdown block:" + f"\n```python\n{prompt.strip()}\n```\n",
                }],
                max_tokens=self.max_new_tokens,
                stop_sequences=["\n```\n", "\nif "],
                **kwargs,
            )
            outputs.append(message.content[0].text)

        return outputs


class GoogleGenAIDecoder(DecoderBase, ABC):

    def __init__(self, name: str, **kwargs) -> None:
        super().__init__(name, **kwargs)
        genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

    def is_direct_completion(self) -> bool:
        return False


class GeminiDecoder(GoogleGenAIDecoder):

    def codegen(self, prompt: str, do_sample: bool = True, num_samples: int = 200) -> List[str]:
        kwargs = {}
        if do_sample:
            assert self.temperature > 0, "Temperature must be positive for sampling"
            kwargs["top_p"] = 0.95
            kwargs["temperature"] = self.temperature
        else:
            self.temperature = 0

        batch_size = min(self.batch_size, num_samples)
        if not do_sample:
            assert batch_size == 1, "Sampling only supports batch size of 1"

        genai_config = genai.GenerationConfig(
            max_output_tokens=self.max_new_tokens,
            **kwargs,
        )

        safety_settings = [
            {
                "category": "HARM_CATEGORY_DANGEROUS",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE",
            },
        ]

        model = genai.GenerativeModel(model_name=self.name, generation_config=genai_config, safety_settings=safety_settings)

        outputs = []
        for _ in range(batch_size):
            while True:
                try:
                    response = model.generate_content("Please generate self-contained code to complete the following problem wrapped in a Python markdown block:" + f"\n```python\n{prompt.strip()}\n```", generation_config=genai_config)
                    output = response.candidates[0].content.parts[0].text
                    outputs.append(output)
                    break
                except Exception as e:
                    if "list index out of range" in str(e):
                        # append dummy response
                        outputs.append("NO_RESPONSE")
                        break
                    else:
                        print(e)
                        continue

        return outputs


def make_model(
    model: str,
    backend: str,
    dataset: str = "bigcodebench",
    batch_size: int = 1,
    temperature: float = 0.0,
    tp=1,
    base_url=None,
    trust_remote_code=False,
    tokenizer_name=None,
    tokenizer_legacy=True,
):
    if backend == "vllm":
        return GeneralVllmDecoder(
            name=model,
            batch_size=batch_size,
            temperature=temperature,
            dataset=dataset,
            tp=tp,
            trust_remote_code=trust_remote_code,
            tokenizer_name=tokenizer_name,
            tokenizer_legacy=tokenizer_legacy,
        )
    elif backend == "hf":
        return GenenralHfTorchDecoder(
            name=model,
            batch_size=batch_size,
            temperature=temperature,
            dataset=dataset,
            trust_remote_code=trust_remote_code,
            tokenizer_name=tokenizer_name,
            tokenizer_legacy=tokenizer_legacy,
        )
    elif backend == "openai":
        return OpenAIChatDecoder(
            name=model,
            batch_size=batch_size,
            temperature=temperature,
            base_url=base_url,
        )
    elif backend == "mistral":
        return MistralChatDecoder(
            name=model,
            batch_size=batch_size,
            temperature=temperature,
        )
    elif backend == "anthropic":
        return AnthropicMessageDecoder(
            name=model,
            batch_size=batch_size,
            temperature=temperature,
        )
    elif backend == "google":
        return GeminiDecoder(
            name=model,
            batch_size=batch_size,
            temperature=temperature,
        )
