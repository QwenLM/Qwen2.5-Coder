## Setup

1. **Create a Conda Environment**
   Use the following command to create and activate a new environment for the DPO training:
   
   ```bash
   conda create -n dpo_env python=3.10
   conda activate dpo_env
   ```
2. **Install Dependencies**
   After activating the environment, install all required dependencies by running:
   
   ```bash
   pip install -r requirements.txt
   ```
3. **Constructing DPO Data**
   Provide the data for DPO trainng as follow:
   the jsonl file contains json object (each line).
   ```json
   {
        {"prompt": "Prompt"},
        {"chosen": "The chosen response"},
        {"rejected": "The rejected response"},
   }
   ```

4. **Training**
   Once the environment is ready and the model paths are configured, run the DPo training by executing the following script:
   
   ```
   DATA_PATH="/path/to/preference/data"
   SFT_MODEL="/path/to/sft/model"
   OUTPUT_DIR="/path/to/output"
   bash ./scripts/dpo_qwencoder.sh
   ```


