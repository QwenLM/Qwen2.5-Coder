## Setup
1. **Create a Conda Environment**
   Use the following command to create and activate a new environment for the SFT training:
   ```bash
   benchmark="eval_plus"
   conda create -n eval_${benchmark}_env python=3.9
   conda activate eval_${benchmark}_env
   cd ${benchmark}
   pip install -r requirements.txt
   ```
   Please setup all evaluation environments in `test.sh`

2. **Install Dependencies**
   After activating the environment, install all required dependencies by running:
   For each 
   ```bash
   pip install -r requirements.txt
   ```

## Evaluation

1. **Model Path Modification**  
   Before running the evaluation script, ensure that the model paths are correctly set. Modify the paths as needed based on your local environment or cloud storage setup.

2. **Run Evaluation**  
   Once the environment is ready and the model paths are configured, run the evaluation suite by executing the following script:
    ```bash
    EVAL_SCRIPT="./evaluate.sh"
    MODEL_DIR="/path/to/Qwen2.5-coder-Instruct/"
    OUTPUT_DIR="/path/to/results/"
    TP=2
    bash ${EVAL_SCRIPT} ${MODEL_DIR} ${OUTPUT_DIR} ${TP}
    ```


