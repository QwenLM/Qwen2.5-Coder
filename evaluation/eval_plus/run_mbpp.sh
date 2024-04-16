mkdir -p results/mbpp

VLLM_N_GPUS=8 python generate.py \
  --model_type codeqwen \
  --model_size base \
  --bs 1 \
  --temperature 0 \
  --n_samples 1 \
  --resume \
  --greedy \
  --root outputs \
  --dataset mbpp


evalplus.evaluate \
  --dataset mbpp \
  --samples outputs/mbpp/codeqwen_base_temp_0.0 > results/mbpp/codeqwen_base.txt


VLLM_N_GPUS=8 python generate.py \
  --model_type codeqwen \
  --model_size chat \
  --bs 1 \
  --temperature 0 \
  --n_samples 1 \
  --resume \
  --greedy \
  --root outputs \
  --dataset mbpp

evalplus.evaluate \
  --dataset mbpp \
  --samples outputs/mbpp/codeqwen_chat_temp_0.0 > results/mbpp/codeqwen_chat.txt

VLLM_N_GPUS=1 python generate.py \
  --model_type codeqwen \
  --model_size chat-awq \
  --bs 1 \
  --temperature 0 \
  --n_samples 1 \
  --resume \
  --greedy \
  --root outputs \
  --dataset mbpp

evalplus.evaluate \
  --dataset mbpp \
  --samples outputs/mbpp/codeqwen_chat-awq_temp_0.0 > results/mbpp/codeqwen_chat-awq.txt
