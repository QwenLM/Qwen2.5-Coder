## Setup

1. **Create a Conda Environment**
   Use the following command to create and activate a new environment for the SFT training:
   
   ```bash
   conda create -n sft_env python=3.9
   conda activate sft_env
   ```
2. **Install Dependencies**
   After activating the environment, install all required dependencies by running:
   
   ```bash
   pip install -r requirements.txt
   ```
3. **Binarize Data**
   Provide the raw data as follows:
   the raw JSONLINE file contains a JSON object (each line). Each sample should follow the following format:
   ```json
   {
        "messages":[
            {"role": "system", "content": "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."},
            {"role": "user", "content": "Write a regex expression to match any letter of the alphabet"},
            {"role": "assistant", "content": "The regex expression to match any letter of the alphabet (either in uppercase or lowercase) is: \n\n```regex\n[a-zA-Z]\n```"},
            {"role": "user", "content": "How about if I only want to match uppercase letters? Can you modify the regex expression for that?"},
            {"role": "assistant", "content": "Sure, the regex expression to match any uppercase letter of the alphabet is:\n\n```regex\n[A-Z]\n```"}
       ],
       "format": "chatml"
   }
   ```
   For the SFT datasets, the raw JSONLINE file follows the following format:
   ```
   {"messages": [sample1...], "format": "chatml"}
   {"messages": [sample2...], "format": "chatml"}
   {"messages": [sample3...], "format": "chatml"}
   ```
   Binarize the raw data:
   
   ```bash
   INPUT_PATH="/path/to/raw/sft.jsonl"
   OUTPUT_PATH="/path/to/processed/sft.jsonl"
   TOKENIZER_PATH="/path/to/pretrained_models/Qwen/Qwen2___5-Coder-1___5B/"
   bash ./scripts/binarize_data.sh ${INPUT_PATH} ${OUTPUT_PATH} ${TOKENIZER_PATH}
   ```
5. **Training**
   Once the environment is ready and the model paths are configured, run the evaluation suite by executing the following script:
   
   ```bash
   DATA_PATH="/path/to/processed/sft.jsonl"
   PRETRAINED_MODEL="/path/to/pretrained_models/Qwen/Qwen2___5-Coder-1___5B/"
   OUTPUT_DIR="/path/to/checkpoints/sft_model/"
   bash ./scripts/sft_qwencoder.sh ${DATA_PATH} ${PRETRAINED_MODEL} ${OUTPUT_DIR}
   ```

6. **Merge Adapter**
   When running sft with lora, merge the base model and the adapters by executing the following script:

   ```bash
   BASE_MODEL_PATH=${1}
   TRAIN_ADAPTERS_PATH=${2}
   OUTPUT_PATH=${3}
   bash ./scripts/merge_adapter.sh ${BASE_MODEL_PATH} ${TRAIN_ADAPTERS_PATH} ${OUTPUT_PATH}
   ```


