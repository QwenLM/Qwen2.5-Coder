SYSTEM_PROMPT = """
You are a code completion assistant.
"""
NORMAL_SYSTEM_PROMPT = """
You are a helpful assistant.
"""
REPO_COMPLETE_TEMPLATE = """
##Context Code##:
{}
##Prefix Code##:
{}
##Suffix Code##:
{}
##Middle Code##:
"""

CODEQWEN_BASE_TEMPLATE="""
{}<fim_prefix>{}<fim_suffix>{}<fim_middle>
"""

QWEN_CODER_TEMPLAT="""
{}<|fim_prefix|>{}<|fim_suffix|>{}<|fim_middle|>
"""

STARCODER_BASE_TEMPLATE= """
{}<fim_prefix>{}<fim_suffix>{}<fim_middle>
"""


STARCODER2_BASE_TEMPLATE= """
{}<fim_prefix>{}<fim_suffix>{}<fim_middle>
"""


DEEPSEEK_CODER_BASE_TEMPLATE= """
{}<｜fim▁begin｜>{}<｜fim▁hole｜>{}<｜fim▁end｜>
"""

CODESTRAL_TEMPLATE= """
{}[PREFIX]{}[SUFFIX]{}[MIDDLE]
"""

CODELLAMA_TEMPLATE= """
{}<PRE> {pre} <SUF>{suf} <MID>
"""
