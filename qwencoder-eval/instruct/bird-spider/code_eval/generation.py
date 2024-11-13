import json
import asyncio
import random

from math import ceil
from openai import AsyncOpenAI
from tqdm import tqdm
from tqdm.asyncio import tqdm_asyncio

from accelerate.utils import set_seed
from torch.utils.data.dataloader import DataLoader
from transformers import StoppingCriteria, StoppingCriteriaList

from code_eval.utils import TokenizedDataset, ChatTokenizedDataset, complete_code


class EndOfFunctionCriteria(StoppingCriteria):
    """Custom `StoppingCriteria` which checks if all generated functions in the batch are completed."""

    def __init__(self, start_length, eof_strings, tokenizer, check_fn=None):
        self.start_length = start_length
        self.eof_strings = eof_strings
        self.tokenizer = tokenizer
        if check_fn is None:
            check_fn = lambda decoded_generation: any([stop_string in decoded_generation for stop_string in self.eof_strings])
        self.check_fn = check_fn

    def __call__(self, input_ids, scores, **kwargs):
        """Returns true if all generated sequences contain any of the end-of-function strings."""
        decoded_generations = self.tokenizer.batch_decode(input_ids[:, self.start_length:])
        return all([self.check_fn(decoded_generation) for decoded_generation in decoded_generations])


class TooLongFunctionCriteria(StoppingCriteria):
    """Custom `StoppingCriteria` which checks if the generated function is too long by a certain multiplier based on input length."""

    def __init__(self, input_length, multiplier):
        self.input_length = input_length
        self.multiplier = multiplier

    def __call__(self, input_ids, scores, **kwargs):
        """Returns true if generated sequence is too long."""
        return input_ids.shape[1] > int(self.input_length * self.multiplier)


def parallel_generations(task, dataset, accelerator, model, tokenizer, n_tasks, args):
    if args.load_generations_path:
        # load generated code
        with open(args.load_generations_path) as fp:
            generations = json.load(fp)
            if accelerator.is_main_process:
                print(f"generations loaded, {n_tasks} selected from {len(generations)} with {len(generations[0])} candidates")
        return generations[:n_tasks]

    set_seed(args.seed, device_specific=True)

    # Setup generation settings
    gen_kwargs = {
        "do_sample": args.do_sample,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "top_k": args.top_k,
        "max_length": args.max_length_input,
        "max_new_tokens": args.max_new_tokens,
        "num_beams": args.num_beams,
        # "repetition_penalty": 1.1,
    }
    stopping_criteria = []
    # The input_length / start_length set to 0 for now will be adjusted later
    # Check if the task has a custom check_fn method for the stopping criteria
    if task.stop_words and tokenizer.eos_token:
        task.stop_words.append(tokenizer.eos_token)
    if hasattr(task, "check_fn"):
        stopping_criteria.append(EndOfFunctionCriteria(0, task.stop_words, tokenizer, task.check_fn))
    elif task.stop_words:
        stopping_criteria.append(EndOfFunctionCriteria(0, task.stop_words, tokenizer))
    if hasattr(task, "max_length_multiplier") and task.max_length_multiplier:
        stopping_criteria.append(TooLongFunctionCriteria(0, task.max_length_multiplier))

    if stopping_criteria:
        gen_kwargs["stopping_criteria"] = StoppingCriteriaList(stopping_criteria)

    if args.instruction_tokens:
        instruction_tokens = args.instruction_tokens.split(",")
        if len(instruction_tokens) != 3:
            raise ValueError("Instruction tokens should contain exactly 3 tokens separated by a comma. If a token is empty, represent it as ''")
        for token in instruction_tokens:
            if token.strip() != "":
                task.stop_words.append(token)
    else:
        instruction_tokens = None
    if accelerator.is_main_process:
        print(f"number of problems for this task is {n_tasks}")
    n_copies = ceil(args.n_samples / args.batch_size)

    if args.chat_mode:
        print(f"Chat-Mode enabled.")
        ds_tokenized = ChatTokenizedDataset(
            accelerator,
            task,
            dataset,
            tokenizer,
            max_length=args.max_length_input,
            limit_start=args.limit_start,
            n_tasks=n_tasks,
            n_copies=n_copies,
        )
    else:
        print("Completion mode (default)")
        ds_tokenized = TokenizedDataset(
            task,
            dataset,
            tokenizer,
            num_devices=accelerator.state.num_processes,
            max_length=args.max_length_input,
            limit_start=args.limit_start,
            n_tasks=n_tasks,
            n_copies=n_copies,
            prefix=args.prefix,
            has_encoder=args.modeltype == "seq2seq",
            instruction_tokens=instruction_tokens,
        )

    # do not confuse args.batch_size, which is actually the num_return_sequences
    ds_loader = DataLoader(ds_tokenized, batch_size=1)

    is_loaded_in_8bit = getattr(model, "is_loaded_in_8bit", False)
    is_loaded_in_4bit = getattr(model, "is_loaded_in_4bit", False)
    if args.max_memory_per_gpu is not None:
        # The model is already sharded across multiple GPUs
        ds_loader = accelerator.prepare(ds_loader)
    elif not is_loaded_in_8bit and not is_loaded_in_4bit:
        # we only wrap data loader to avoid extra memory occupation

        # this line is commented
        # due to "device_map": "auto"
        # model = model.to(accelerator.device)
        ds_loader = accelerator.prepare(ds_loader)
    else:
        # model.to() is not supported for 8bit and 4bit models
        model, ds_loader = accelerator.prepare(model, ds_loader)

    generations = complete_code(
        task,
        accelerator,
        model,
        tokenizer,
        ds_loader,
        n_tasks=n_tasks,
        limit_start=args.limit_start,
        batch_size=args.batch_size,
        prefix=args.prefix,
        instruction_tokens=instruction_tokens,
        postprocess=args.postprocess,
        is_wrapped=is_loaded_in_8bit or is_loaded_in_4bit,
        **gen_kwargs,
    )
    return generations


EOS = [
    ";",
    "<pad>",
    "<|endoftext|>",
    "</s>",
    "<|im_end|>",
]

OPENAI_EOS = [
    ";",
    "<|endoftext|>",
    "</s>",
    "<|im_end|>",
]
from vllm import SamplingParams


def vllm_generation(task, dataset, model, tokenizer, n_tasks, args):
    prompts = []
    for i in range(len(dataset)):
        prompt_contents = task.get_prompt(dataset[i])
        prompt = [{"role": "user", "content": prompt_contents}]
        prompts.append(prompt)

    chat_prompts = []
    for prompt in prompts:
        chat_prompts.append(tokenizer.apply_chat_template(
            prompt,
            tokenize=False,
            add_generation_prompt=True,
        ))

    print("Chat prompts:")
    print(chat_prompts[0])

    vllm_outputs = model.generate(
        prompts=chat_prompts,
        sampling_params=SamplingParams(
            max_tokens=4096,
            temperature=0.0,
            top_p=1.0,
            stop=EOS,
        ),
        use_tqdm=True,
    )

    raw_generations = [x.outputs[0].text for x in vllm_outputs]
    gen_strs = [task.postprocess_generation(x, id) for id, x in enumerate(raw_generations)]
    generations = [[gen_strs[i]] for i in range(len(gen_strs))]

    print("Raw Generations:")
    print(raw_generations[0])

    print("Generations:")
    print(gen_strs[0])

    return generations


async def openai_generation(task, dataset, model: AsyncOpenAI, tokenizer, n_tasks, args):
    prompts = []
    for i in range(len(dataset)):
        prompt_contents = task.get_prompt(dataset[i])
        prompt = [{"role": "user", "content": prompt_contents}]
        prompts.append(prompt)

    print("Prompts:")
    print(prompts[0])

    async def generate_async(prompt):
        while True:
            try:
                response = await model.chat.completions.create(
                    model=args.model,
                    messages=prompt,
                    temperature=0.0,
                    top_p=1.0,
                    max_tokens=4096,
                    stop=OPENAI_EOS,
                )
                return response.choices[0].message.content
            except Exception as e:
                print(e)
                print("Retrying...")
                # random sleep to avoid rate limiting
                await asyncio.sleep(random.randint(5, 15))

    raw_generations = []
    async_responses = []
    for prompt in tqdm(prompts):
        gen = asyncio.create_task(generate_async(prompt))
        async_responses.append(gen)
    raw_generations = await tqdm_asyncio.gather(*async_responses)

    gen_strs = [task.postprocess_generation(x, id) for id, x in enumerate(raw_generations)]
    generations = [[gen_strs[i]] for i in range(len(gen_strs))]

    print("Raw Generations:")
    print(raw_generations[0])

    print("Generations:")
    print(gen_strs[0])

    return generations
