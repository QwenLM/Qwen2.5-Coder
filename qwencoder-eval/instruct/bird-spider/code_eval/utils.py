import math
import warnings
from collections import defaultdict

import torch
from torch.utils.data import IterableDataset
from tqdm import tqdm

INFILL_MODE = False
INSTRUCTION_MODE = False


class TokenizedDataset(IterableDataset):
    """Tokenize and preprocess the dataset
    Multiple copies of the same prompt are sent sequentially. See compute_code for more details.
    The prompt can either be:
    - one prompt: normal code completion
    - two prompts: for infilling mode (prefix, suffix) or instructin-tuning mode (instruction, context)
    """

    def __init__(
        self,
        task,
        dataset,
        tokenizer,
        num_devices,
        max_length,
        limit_start=0,
        n_tasks=None,
        n_copies=1,
        prefix="",
        has_encoder=False,
        instruction_tokens=None,
    ):
        self.task = task
        self.dataset = dataset
        self.tokenizer = tokenizer
        self.num_devices = num_devices
        self.max_length = max_length
        self.limit_start = limit_start
        self.n_tasks = n_tasks
        self.n_copies = n_copies
        self.prefix = prefix
        self.has_encoder = has_encoder
        self.instruction_tokens = instruction_tokens

    def __iter__(self):
        prompts = []
        prompts_encoder = []
        infill = []
        instruction = []
        for sample in range(self.limit_start, self.limit_start + self.n_tasks):
            prompt_contents = self.task.get_prompt(self.dataset[sample])
            if isinstance(prompt_contents, str):
                # Normal code completion mode
                infill.append(False)
                instruction.append(False)
                prompt = self.prefix + prompt_contents
            elif isinstance(prompt_contents, dict):
                if set(prompt_contents.keys()) == {"prefix", "suffix"}:
                    # Infilling mode
                    infill.append(True)
                    instruction.append(False)
                    prompt = self._make_infill_prompt(**prompt_contents, preprefix=self.prefix)
                elif set(prompt_contents.keys()) == {"instruction", "context"}:
                    # Instruction-tuning mode
                    instruction.append(True)
                    infill.append(False)
                    prompt = self._make_instruction_prompt(**prompt_contents, prefix=self.prefix)
            else:
                raise ValueError(f"Unsupported prompt format: {type(prompt_contents)}")
            prompts.append(prompt)
            if self.has_encoder:
                prompt_encoder = self.task.get_prompt_encoder(self.dataset[sample])
                if isinstance(prompt_encoder, str):
                    prompt_encoder = self.prefix + prompt_encoder
                prompts_encoder.append(prompt_encoder)

        if not len(set(infill)) == 1 or not len(set(instruction)) == 1:
            raise ValueError("Mixed infill/instruction and completion prompts are not supported.")
        global INFILL_MODE
        global INSTRUCTION_MODE
        INFILL_MODE = infill[0]
        INSTRUCTION_MODE = instruction[0]
        if INFILL_MODE:
            return_token_type_ids = False
        else:
            return_token_type_ids = None  # default

        outputs = self.tokenizer(
            prompts,
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=self.max_length,
            return_token_type_ids=return_token_type_ids,
        )
        if self.has_encoder:
            outputs_encoder = self.tokenizer(
                prompts_encoder,
                padding=True,
                truncation=True,
                return_tensors="pt",
                max_length=self.max_length,
                return_token_type_ids=return_token_type_ids,
            )

        # if self.n_copies == 1 and self.n_tasks % self.num_devices != 0:
        #     self.n_copies = 2
        #     warnings.warn(
        #         "n_copies (n_samples/batch_size) was changed from 1 to 2 because n_tasks isn't proportional to num devices"
        #     )

        for sample in range(self.n_tasks):
            for _ in range(self.n_copies):
                if self.has_encoder:
                    yield {
                        "ids": outputs.input_ids[sample],
                        "ids_encoder": outputs_encoder.input_ids[sample],
                        "task_id": sample,
                        "input_len": outputs.attention_mask[sample].sum(),
                        "input_len_encoder": outputs_encoder.attention_mask[sample].sum(),
                    }
                else:
                    yield {
                        "ids": outputs.input_ids[sample],
                        "task_id": sample,
                        "input_len": outputs.attention_mask[sample].sum(),
                    }

    def _make_infill_prompt(self, prefix, suffix, preprefix=""):
        """Make a prompt for infilling.
        Currently supported only for official InCoder and SantaCoder implementations.
        """
        model_id = self.tokenizer.name_or_path
        if model_id in ["facebook/incoder-1B", "facebook/incoder-6B"]:
            self.tokenizer.add_special_tokens({"pad_token": "<pad>"})
            return f"{preprefix}{prefix}<|mask:0|>{suffix}<|mask:0|>"
        elif model_id in ["bigcode/santacoder"]:
            return f"<fim-prefix>{preprefix}{prefix}<fim-suffix>{suffix}<fim-middle>"
        elif model_id in ["bigcode/starcoder", "bigcode/starcoderbase"]:
            return f"<fim_prefix>{preprefix}{prefix}<fim_suffix>{suffix}<fim_middle>"
        else:
            raise ValueError(f"Infilling not yet supported for: {model_id}")

    def _make_instruction_prompt(self, instruction, context, prefix=""):
        """Make a prompt for instruction-tuning. Delimit instruction and context with specific tokens if provided."""
        if not self.instruction_tokens:
            warnings.warn("Instruction-tuning tokens are not provided for an instruction-tuning task, we will leave them empty.")
            user_token, end_token, assistant_token = "", "", "\n"
        else:
            user_token, end_token, assistant_token = self.instruction_tokens
            if not user_token or not assistant_token or not end_token:
                warnings.warn("Instruction-tuning tokens provided but one or more are empty. Ignore warning if this was intended")
        prompt = prefix + user_token + instruction + end_token + assistant_token + context

        return prompt


class ChatTokenizedDataset(IterableDataset):

    def __init__(
        self,
        accelerator,
        task,
        dataset,
        tokenizer,
        max_length,
        limit_start=0,
        n_tasks=None,
        n_copies=1,
    ):
        self.accelerator = accelerator
        self.task = task
        self.dataset = dataset
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.limit_start = limit_start
        self.n_tasks = n_tasks
        self.n_copies = n_copies

    def __iter__(self):
        prompts = []
        for sample in range(self.limit_start, self.limit_start + self.n_tasks):
            prompt_contents = self.task.get_prompt(self.dataset[sample])
            if isinstance(prompt_contents, str):
                prompt = [{"role": "user", "content": prompt_contents}]
            else:
                raise ValueError(f"Unsupported prompt format: {type(prompt_contents)}")

            prompts.append(prompt)

        ds_input_ids, ds_attn_mask = [], []
        input_str_lens = []
        for one_msg in prompts:
            outputs = self.tokenizer.apply_chat_template(
                one_msg,
                padding=True,
                truncation=True,
                tokenize=True,
                add_generation_prompt=True,
                return_tensors="pt",
                max_length=self.max_length,
                return_dict=True,
            )

            encoded_tokens = self.tokenizer.apply_chat_template(
                one_msg,
                padding=False,
                truncation=True,
                tokenize=True,
                add_generation_prompt=True,
                return_tensors="pt",
                max_length=self.max_length,
            )[0]

            if encoded_tokens[0] == self.tokenizer.bos_token_id:
                encoded_tokens = encoded_tokens[1:]

            input_str_lens.append(len(self.tokenizer.decode(encoded_tokens)))
            if not len(ds_input_ids):
                print("Before:")
                print(one_msg)
                print("After:")
                print(self.tokenizer.decode(encoded_tokens))

            ds_input_ids.append(outputs.input_ids[0])
            ds_attn_mask.append(outputs.attention_mask[0])

        # outputs = self.tokenizer.apply_chat_template(
        #     prompts,
        #     padding=True,
        #     truncation=True,
        #     tokenize=True,
        #     add_generation_prompt=True,
        #     return_tensors="pt",
        #     max_length=self.max_length,
        #     return_dict=True,
        # )

        # print("[1]", prompts[0])
        # print("[2]", self.tokenizer.decode(ds_input_ids[0]))

        for sample in range(self.n_tasks):
            input_str = self.tokenizer.decode(ds_input_ids[sample])
            self.dataset[self.limit_start + sample]["input_str_len"] = input_str_lens[sample]
            # self.dataset[self.limit_start + sample]["input_str_len"]= len(input_str)
            for _ in range(self.n_copies):
                yield {
                    "ids": ds_input_ids[sample],
                    "task_id": sample,
                    "input_len": ds_attn_mask[sample].sum(),
                }


def _parse_infill(code, tokenizer):
    """Reorder infill code and remove remaining special tokens."""
    model_id = tokenizer.name_or_path
    if model_id in ["facebook/incoder-1B", "facebook/incoder-6B"]:
        prefix, suffix, infill = code.split("<|mask:0|>", 2)
        infill = infill.split("<|endofmask|>")[0]
    elif model_id in ["bigcode/santacoder"]:
        prefix, rest = code.split("<fim-suffix>", 1)
        suffix, infill = rest.split("<fim-middle>", 1)
        infill = infill.split("<|endoftext|>")[0]
    elif model_id in ["bigcode/starcoder", "bigcode/starcoderbase"]:
        prefix, rest = code.split("<fim_suffix>", 1)
        suffix, infill = rest.split("<fim_middle>", 1)
        infill = infill.split("<|endoftext|>")[0]
    else:
        raise ValueError(f"Infilling not yet supported for: {model_id}")
    for k, v in tokenizer.special_tokens_map.items():
        if k == "additional_special_tokens":
            for t in v:
                infill = infill.replace(t, "")
        else:
            infill = infill.replace(v, "")
    return infill


def _parse_instruction(code, instruction_tokens):
    """Return code block after assistant_token/end_token"""
    _, end_token, assistant_token = instruction_tokens
    if not assistant_token and end_token:
        assistant_token = end_token
    elif not assistant_token and not end_token:
        return code

    idx = code.find(assistant_token)
    shift = len(assistant_token)
    if idx == -1:
        warnings.warn("The assistant token was not detected in the generation, this might disrupt the post-processing and lead to lower evaluation scores")
        return code

    if "```python" in assistant_token:
        idx = code.find("```python", idx)
        shift = len("```python")
    return code[idx + shift:]


def complete_code(
    task,
    accelerator,
    model,
    tokenizer,
    dataloader,
    n_tasks,
    limit_start=0,
    batch_size=20,
    prefix="",
    instruction_tokens=None,
    postprocess=True,
    is_wrapped=False,
    **gen_kwargs,
):
    """Generate multiple codes for each task in the dataset using multiple GPUs with accelerate.
    dataloader sends all the prompts from the evalution dataset to the model as the following:
    [p_0_0, p_0_1, ..., p_0_nc-1, p_1_0, ..., p_nt-1_nc-1] where nc is the number of copies of the prompt,
    and nt is the number of tasks. nc is such that num_samples(for each task)= nc * batch_size
    """

    gen_token_dict = defaultdict(list)  # dict of list of generated tokens
    for step, batch in tqdm(
            enumerate(dataloader),
            total=math.ceil(n_tasks * dataloader.dataset.n_copies / accelerator.num_processes),
    ):
        with torch.no_grad():
            if task.stop_words:
                # Set the start_length after which to check for stopping to be the longest input ignoring padding
                max_len = batch["input_len"].max().item()
                if "ids_encoder" in batch:
                    max_len += 1  # Add 1 for decoder_start_token_id
                gen_kwargs["stopping_criteria"][0].start_length = max_len
            if hasattr(task, "max_length_multiplier") and task.max_length_multiplier:
                idx = 1 if task.stop_words else 0
                gen_kwargs["stopping_criteria"][idx].input_length = batch["input_len"].max().item()

            inputs = batch["ids"][:, :batch["input_len"]] if tokenizer.padding_side == "right" else batch["ids"]

            copied_kwargs = gen_kwargs.copy()
            target_beam = copied_kwargs.pop("num_beams")
            for trying_num_beams in range(target_beam, 0, -1):
                # print(f"[{accelerator.process_index}] Ready to test {trying_num_beams}:")
                try:
                    if is_wrapped:
                        # 8bit and 4bit models are wrapped in accelerator
                        generated_tokens = accelerator.unwrap_model(model).generate(
                            input_ids=inputs,
                            num_return_sequences=trying_num_beams,
                            num_beams=trying_num_beams,
                            **copied_kwargs,
                        )
                    else:
                        generated_tokens = model.generate(
                            input_ids=inputs,
                            num_return_sequences=trying_num_beams,
                            num_beams=trying_num_beams,
                            **copied_kwargs,
                        )
                        # print(f"[{accelerator.process_index}] Try {trying_num_beams} success!")
                    padded_tokens = generated_tokens[-1].unsqueeze(0).repeat_interleave(target_beam - trying_num_beams, dim=0)
                    generated_tokens = torch.cat((generated_tokens, padded_tokens))
                    break
                except RuntimeError as e:
                    if "out of memory" not in str(e):
                        raise RuntimeError(e)
                    if trying_num_beams == 1:
                        # generated_tokens =
                        # print(f"[{accelerator.process_index}] {inputs.size() = }")
                        # raise RuntimeError(e)
                        generated_tokens = inputs.repeat_interleave(batch_size, dim=0)
                    torch.cuda.empty_cache()
                    # print(f"[{accelerator.process_index}] Try {trying_num_beams} failed...")

            # each task is generated batch_size times
            generated_tasks = batch["task_id"].repeat(batch_size)
            generated_tokens = accelerator.pad_across_processes(generated_tokens, dim=1, pad_index=tokenizer.pad_token_id)

            # print(f"[{accelerator.process_index}] Before: {generated_tokens.size()}")
            generated_tokens, generated_tasks = accelerator.gather((generated_tokens, generated_tasks))
            # print(f"[{accelerator.process_index}] After: {generated_tokens.size()}")
            generated_tokens = generated_tokens.cpu().numpy()
            generated_tasks = generated_tasks.cpu().numpy()

            for sample, generated_tokens in zip(generated_tasks, generated_tokens):
                gen_token_dict[sample].append(generated_tokens)

    code_gens = [[] for _ in range(n_tasks)]
    for sample, generated_tokens in gen_token_dict.items():
        for s in generated_tokens:
            if INFILL_MODE or tokenizer.eos_token in task.stop_words:
                if s[0] == tokenizer.bos_token_id:
                    s = s[1:]
                # Treat eos token as a regular stop word not removing it from the output
                # If it's removed it may have the effect of removing it in the middle of a
                # longer generation in case a batch size > 1 is used, which will result in
                # a wrong generation as it won't be used for splitting lateron
                gen_code = tokenizer.decode(s, skip_special_tokens=False, clean_up_tokenization_spaces=False)
                try:
                    # some tokenizers add a multi-token prefix to the generation (e.g ChatGLM)
                    tokenizer_prefix = tokenizer.decode(tokenizer.get_prefix_tokens())
                    if gen_code.startswith(f"{tokenizer_prefix}"):
                        gen_code = gen_code[len(tokenizer_prefix):].lstrip()
                except:
                    pass
                if INFILL_MODE:
                    gen_code = _parse_infill(gen_code, tokenizer)
                if INSTRUCTION_MODE:
                    gen_code = _parse_instruction(gen_code, instruction_tokens)
            else:
                gen_code = tokenizer.decode(s, skip_special_tokens=True, clean_up_tokenization_spaces=True)
            if not INFILL_MODE:
                gen_code = gen_code[len(prefix):]
            if postprocess:
                code_gens[sample].append(task.postprocess_generation(gen_code, int(sample) + limit_start))
            else:
                warnings.warn("model output is not postprocessed, this might lower evaluation scores")
                code_gens[sample].append(gen_code)

    return code_gens


import re


def remove_after_return(code):
    """
    Takes as input a code, and removes everything that is after the return.
    That is, the first line that does not start with a space character
    """
    pattern = r"[^\n]+(\n|$)"
    end_last_match = None
    # Go trough the regex to match any sequence of characters ending with a \n
    for match in re.finditer(pattern, code):
        start_match, end_match = match.span()
        # Search for the first line which does not start by a space character
        if end_last_match is not None and start_match < len(code) and code[start_match].strip() != "":
            return code[0:start_match]
        end_last_match = end_match
    return code
