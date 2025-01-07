from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class LMStyle(Enum):
    QwenQwQPreview = "QwenQwQPreview"

    CodeQwenBase = "CodeQwenBase"
    CodeQwenChat = "CodeQwenChat"

    OpenAIChat = "OpenAIChat"
    Anthropic = "Anthropic"
    AnthropicMessage = "AnthropicMessage"
    Gemini = "Gemini"
    MistralWeb = "MistralWeb"

    DeepSeekBase = "DeepSeekBase"
    CodeLLaMaBase = "CodeLLaMaBase"
    StarCoder2Base = "StarCoder2Base"
    StableCodeBase = "StableCodeBase"

    DeepSeekCodeInstruct = "DeepSeekCodeInstruct"
    CodeLLaMaInstruct = "CodeLLaMaInstruct"

    Phind = "Phind"
    WizardCoder = "WizardCoder"
    MagiCoder = "MagiCoder"
    OC = "OC"


@dataclass
class LanguageModel:
    model_name: str
    model_repr: str
    model_style: LMStyle
    release_date: datetime | None  # XXX Should we use timezone.utc?
    link: str | None = None

    def __hash__(self) -> int:
        return hash(self.model_name)


LanguageModelList: list[LanguageModel] = [
    LanguageModel(
        "Qwen/QwQ-32B-Preview",
        "Qwen-QwQ-32B-Preview",
        LMStyle.QwenQwQPreview,
        datetime(2024, 11, 21),
        link=None,
    ),
    LanguageModel(
        "Qwen/CodeQwen1.5-7B",
        "CodeQwen1.5-7B",
        LMStyle.CodeQwenBase,
        datetime(2024, 4, 16),
        link="https://huggingface.co/Qwen/CodeQwen1.5-7B",
    ),
    LanguageModel(
        "Qwen/CodeQwen1.5-7B-Chat",
        "CodeQwen1.5-7B-Chat",
        LMStyle.CodeQwenChat,
        datetime(2024, 4, 16),
        link="https://huggingface.co/Qwen/CodeQwen1.5-7B-Chat",
    ),
    LanguageModel(
        "deepseek-ai/deepseek-coder-33b-instruct",
        "DSCoder-33b-Ins",
        LMStyle.DeepSeekCodeInstruct,
        datetime(2023, 9, 1),
        link="https://huggingface.co/deepseek-ai/deepseek-coder-33b-instruct",
    ),
    LanguageModel(
        "deepseek-ai/deepseek-coder-6.7b-instruct",
        "DSCoder-6.7b-Ins",
        LMStyle.DeepSeekCodeInstruct,
        datetime(2023, 9, 1),
        link="https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-instruct",
    ),
    LanguageModel(
        "deepseek-ai/deepseek-coder-1.3b-instruct",
        "DSCoder-1.3b-Ins",
        LMStyle.DeepSeekCodeInstruct,
        datetime(2023, 8, 1),
        link="https://huggingface.co/deepseek-ai/deepseek-coder-1.3b-instruct",
    ),
    LanguageModel(
        "codellama/CodeLlama-34b-Instruct-hf",
        "Cllama-34b-Ins",
        LMStyle.CodeLLaMaInstruct,
        datetime(2023, 1, 1),
        link="https://huggingface.co/codellama/CodeLlama-34b-Instruct-hf",
    ),
    LanguageModel(
        "codellama/CodeLlama-13b-Instruct-hf",
        "Cllama-13b-Ins",
        LMStyle.CodeLLaMaInstruct,
        datetime(2023, 1, 1),
        link="https://huggingface.co/codellama/CodeLlama-13b-Instruct-hf",
    ),
    LanguageModel(
        "codellama/CodeLlama-7b-Instruct-hf",
        "Cllama-7b-Ins",
        LMStyle.CodeLLaMaInstruct,
        datetime(2023, 1, 1),
        link="https://huggingface.co/codellama/CodeLlama-7b-Instruct-hf",
    ),
    LanguageModel(
        "WizardCoderLM/WizardCoderCoder-Python-34B-V1.0",
        "WCoder-34B-V1",
        LMStyle.WizardCoder,
        datetime(2023, 1, 1),
        link="https://huggingface.co/WizardCoderLM/WizardCoderCoder-Python-34B-V1.0",
    ),
    LanguageModel(
        "WizardCoderLM/WizardCoderCoder-33B-V1.1",
        "WCoder-33B-V1.1",
        LMStyle.WizardCoder,
        datetime(2023, 9, 1),
        link="https://huggingface.co/WizardCoderLM/WizardCoderCoder-33B-V1.1",
    ),
    LanguageModel(
        "Phind/Phind-CodeLlama-34B-v2",
        "Phind-34B-V2",
        LMStyle.Phind,
        datetime(2023, 1, 1),
        link="https://huggingface.co/Phind/Phind-CodeLlama-34B-v2",
    ),
    LanguageModel(
        "gpt-3.5-turbo-0301",
        "GPT-3.5-Turbo-0301",
        LMStyle.OpenAIChat,
        datetime(2021, 10, 1),
        link="https://openai.com/blog/new-models-and-developer-products-announced-at-devday",
    ),
    LanguageModel(
        "gpt-3.5-turbo-0125",
        "GPT-3.5-Turbo-0125",
        LMStyle.OpenAIChat,
        datetime(2021, 10, 1),
        link="https://openai.com/blog/new-embedding-models-and-api-updates#:~:text=Other%20new%20models%20and%20lower%20pricing",
    ),
    LanguageModel(
        "gpt-4-0613",
        "GPT-4-0613",
        LMStyle.OpenAIChat,
        datetime(2021, 10, 1),
        link="https://openai.com/blog/new-models-and-developer-products-announced-at-devday",
    ),
    LanguageModel(
        "gpt-4-1106-preview",
        "GPT-4-Turbo-1106",
        LMStyle.OpenAIChat,
        datetime(2023, 4, 30),
        link="https://openai.com/blog/new-models-and-developer-products-announced-at-devday",
    ),
    LanguageModel(
        "claude-2",
        "Claude-2",
        LMStyle.Anthropic,
        datetime(2022, 12, 31),
        link="https://www.anthropic.com/index/claude-2",
    ),
    LanguageModel(
        "claude-instant-1",
        "Claude-Instant-1",
        LMStyle.Anthropic,
        datetime(2022, 12, 31),
        link="https://www.anthropic.com/index/introducing-claude",
    ),
    LanguageModel(
        "claude-3-opus-20240229",
        "Claude-3-Opus",
        LMStyle.AnthropicMessage,
        datetime(2023, 9, 1),
        link="https://www.anthropic.com/index/claude-3",
    ),
    LanguageModel(
        "claude-3-sonnet-20240229",
        "Claude-3-Sonnet",
        LMStyle.AnthropicMessage,
        datetime(2023, 9, 1),
        link="https://www.anthropic.com/index/claude-3",
    ),
    LanguageModel(
        "gemini-pro",
        "Gemini-Gemini-Pro",
        LMStyle.Gemini,
        datetime(2023, 5, 1),
        link="https://blog.Gemini/technology/ai/gemini-api-developers-cloud",
    ),
    LanguageModel(
        "ise-uiuc/Magicoder-S-DS-6.7B",
        "MagiCoderS-DS-6.7B",
        LMStyle.MagiCoder,
        datetime(2023, 7, 30),
        link="https://huggingface.co/ise-uiuc/Magicoder-S-DS-6.7B",
    ),
    LanguageModel(
        "ise-uiuc/Magicoder-S-CL-7B",
        "MagiCoderS-CL-7B",
        LMStyle.MagiCoder,
        datetime(2023, 1, 1),
        link="https://huggingface.co/ise-uiuc/Magicoder-S-CL-7B",
    ),
    LanguageModel(
        "bigcode/starcoder2-3b",
        "StarCoder2-3b",
        LMStyle.StarCoder2Base,
        datetime(2023, 1, 1),
        link="https://huggingface.co/bigcode/starcoder2-7b-magicoder-instruct/tree/main",
    ),
    LanguageModel(
        "bigcode/starcoder2-7b",
        "StarCoder2-7b",
        LMStyle.StarCoder2Base,
        datetime(2023, 1, 1),
        link="https://huggingface.co/bigcode/starcoder2-7b-magicoder-instruct/tree/main",
    ),
    LanguageModel(
        "bigcode/starcoder2-15b",
        "StarCoder2-15b",
        LMStyle.StarCoder2Base,
        datetime(2023, 1, 1),
        link="https://huggingface.co/bigcode/starcoder2-7b-magicoder-instruct/tree/main",
    ),
    LanguageModel(
        "codellama/CodeLlama-34b-hf",
        "CodeLlama-34b-Base",
        LMStyle.CodeLLaMaBase,
        datetime(2023, 1, 1),
        link="https://huggingface.co/codellama/CodeLlama-34b-hf",
    ),
    LanguageModel(
        "codellama/CodeLlama-13b-hf",
        "CodeLlama-13b-Base",
        LMStyle.CodeLLaMaBase,
        datetime(2023, 1, 1),
        link="https://huggingface.co/codellama/CodeLlama-13b-hf",
    ),
    LanguageModel(
        "codellama/CodeLlama-7b-hf",
        "CodeLlama-7b-Base",
        LMStyle.CodeLLaMaBase,
        datetime(2023, 1, 1),
        link="https://huggingface.co/codellama/CodeLlama-7b-hf",
    ),
    LanguageModel(
        "deepseek-ai/deepseek-coder-33b-base",
        "DSCoder-33b-Base",
        LMStyle.DeepSeekBase,
        datetime(2023, 1, 1),
        link="https://huggingface.co/deepseek-ai/deepseek-coder-33b-base",
    ),
    LanguageModel(
        "deepseek-ai/deepseek-coder-6.7b-base",
        "DSCoder-6.7b-Base",
        LMStyle.DeepSeekBase,
        datetime(2023, 1, 1),
        link="https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-base",
    ),
    LanguageModel(
        "deepseek-ai/deepseek-coder-1.3b-base",
        "DSCoder-1.3b-Base",
        LMStyle.DeepSeekBase,
        datetime(2023, 1, 1),
        link="https://huggingface.co/deepseek-ai/deepseek-coder-1.3b-base",
    ),
    LanguageModel(
        "mistral-large-latest",
        "Mistral-Large",
        LMStyle.MistralWeb,
        datetime(2023, 1, 1),
        link="https://mistral.ai/news/mistral-large/",
    ),
    LanguageModel(
        "m-a-p/OpenCodeInterpreter-DS-33B",
        "OC-DS-33B",
        LMStyle.OC,
        datetime(2023, 1, 1),
        link="https://huggingface.co/m-a-p/OpenCodeInterpreter-DS-33B/",
    ),
    LanguageModel(
        "m-a-p/OpenCodeInterpreter-DS-6.7B",
        "OC-DS-6.7B",
        LMStyle.OC,
        datetime(2023, 9, 1),
        link="https://huggingface.co/m-a-p/OpenCodeInterpreter-DS-6.7B/",
    ),
    LanguageModel(
        "m-a-p/OpenCodeInterpreter-DS-1.3B",
        "OC-DS-1.3B",
        LMStyle.OC,
        datetime(2023, 9, 1),
        link="https://huggingface.co/m-a-p/OpenCodeInterpreter-DS-1.3B/",
    ),
    LanguageModel(
        "stabilityai/stable-code-3b",
        "StableCode-3B",
        LMStyle.StableCodeBase,
        datetime(2023, 9, 1),
        link="https://huggingface.co/stabilityai/stable-code-3b/",
    ),
]

LanguageModelStore: dict[str, LanguageModel] = {lm.model_name: lm for lm in LanguageModelList}

if __name__ == "__main__":
    print(list(LanguageModelStore.keys()))
