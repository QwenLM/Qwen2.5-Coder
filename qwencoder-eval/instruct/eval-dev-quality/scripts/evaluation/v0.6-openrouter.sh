#!/bin/bash

REVISION="197ece8"
RESULTS="./docs/reports/v0.6"

make install

eval-dev-quality evaluate \
	--runtime docker \
	--runtime-image ghcr.io/symflower/eval-dev-quality:$REVISION \
	--result-path $RESULTS \
	--runs 5 \
	--parallel 20 \
	--model openrouter/01-ai/yi-34b-chat \
	--model openrouter/ai21/jamba-instruct \
	--model openrouter/alpindale/goliath-120b \
	--model openrouter/alpindale/magnum-72b \
	--model openrouter/anthropic/claude-3-haiku \
	--model openrouter/anthropic/claude-3-opus \
	--model openrouter/anthropic/claude-3-sonnet \
	--model openrouter/anthropic/claude-3.5-sonnet \
	--model openrouter/austism/chronos-hermes-13b \
	--model openrouter/cognitivecomputations/dolphin-llama-3-70b \
	--model openrouter/cognitivecomputations/dolphin-mixtral-8x22b \
	--model openrouter/cognitivecomputations/dolphin-mixtral-8x7b \
	--model openrouter/cohere/command-r-03-2024 \
	--model openrouter/cohere/command-r-08-2024 \
	--model openrouter/cohere/command-r-plus-04-2024 \
	--model openrouter/cohere/command-r-plus-08-2024 \
	--model openrouter/databricks/dbrx-instruct \
	--model openrouter/deepseek/deepseek-chat \
	--model openrouter/deepseek/deepseek-coder \
	--model openrouter/google/gemini-flash-1.5 \
	--model openrouter/google/gemini-pro-1.5 \
	--model openrouter/google/gemma-2-27b-it \
	--model openrouter/google/gemma-2-9b-it \
	--model openrouter/google/palm-2-chat-bison \
	--model openrouter/google/palm-2-codechat-bison \
	--model openrouter/meta-llama/llama-3-70b-instruct \
	--model openrouter/meta-llama/llama-3-8b-instruct \
	--model openrouter/meta-llama/llama-3.1-405b-instruct \
	--model openrouter/meta-llama/llama-3.1-70b-instruct \
	--model openrouter/meta-llama/llama-3.1-8b-instruct \
	--model openrouter/microsoft/phi-3-medium-128k-instruct \
	--model openrouter/microsoft/phi-3-medium-4k-instruct \
	--model openrouter/microsoft/phi-3-mini-128k-instruct \
	--model openrouter/microsoft/wizardlm-2-7b \
	--model openrouter/microsoft/wizardlm-2-8x22b \
	--model openrouter/mistralai/codestral-mamba \
	--model openrouter/mistralai/mistral-7b-instruct-v0.3 \
	--model openrouter/mistralai/mistral-large \
	--model openrouter/mistralai/mistral-medium \
	--model openrouter/mistralai/mistral-nemo \
	--model openrouter/mistralai/mistral-small \
	--model openrouter/mistralai/mistral-tiny \
	--model openrouter/mistralai/mixtral-8x22b-instruct \
	--model openrouter/mistralai/mixtral-8x7b-instruct \
	--model openrouter/neversleep/llama-3-lumimaid-70b \
	--model openrouter/neversleep/llama-3-lumimaid-8b \
	--model openrouter/nousresearch/hermes-2-pro-llama-3-8b \
	--model openrouter/nousresearch/hermes-2-theta-llama-3-8b \
	--model openrouter/nousresearch/nous-hermes-2-mixtral-8x7b-dpo \
	--model openrouter/nousresearch/nous-hermes-yi-34b \
	--model openrouter/openai/gpt-4-turbo \
	--model openrouter/openai/gpt-4o \
	--model openrouter/openai/gpt-4o-mini \
	--model openrouter/openchat/openchat-8b \
	--model openrouter/perplexity/llama-3-sonar-large-32k-chat \
	--model openrouter/perplexity/llama-3-sonar-small-32k-chat \
	--model openrouter/qwen/qwen-110b-chat \
	--model openrouter/qwen/qwen-2-72b-instruct \
	--model openrouter/qwen/qwen-2-7b-instruct \
	--model openrouter/qwen/qwen-72b-chat \
	--model openrouter/recursal/eagle-7b \
	--model openrouter/recursal/rwkv-5-3b-ai-town \
	--model openrouter/rwkv/rwkv-5-world-3b \
	--model openrouter/teknium/openhermes-2.5-mistral-7b \
	--model openrouter/togethercomputer/stripedhyena-nous-7b \
	--model openrouter/undi95/toppy-m-7b \
	--model openrouter/xwin-lm/xwin-lm-70b
