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

## Quantization Evaluation Results


### Python

|                                            |  HE  | HE+  | MBPP | MBPP+ | BCB-inst-full | BCB-inst-hard | LCB (2407-2411) |
|--------------------------------------------|:----:|:----:|:----:|:-----:|:-------------:|:-------------:|:---------------:|
| **Qwen2.5-Coder-32B-Instruct**             | 92.7 | 87.2 | 90.2 | 75.1  |     49.6      |     27.0      |      31.4       |
| **Qwen2.5-Coder-32B-AWQ**                  | 92.1 | 84.1 | 87.8 | 75.1  |     48.9      |     27.0      |      31.7       |
| **Qwen2.5-Coder-32B-Instruct-GPTQ-Int8**   | 92.1 | 85.4 | 90.5 | 76.5  |     48.6      |     26.4      |      30.7       |
| **Qwen2.5-Coder-32B-Instruct-GPTQ-Int4**   | 89.6 | 83.5 | 87.0 | 75.9  |     49.7      |     27.0      |      30.3       |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q8_0**   | 90.9 | 86.0 | 89.4 | 76.2  |     47.7      |     23.6      |      31.1       |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q6_K**   | 90.2 | 86.0 | 89.7 | 76.2  |     48.3      |     25.7      |      31.6       |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q5_K_M** | 90.9 | 85.4 | 89.2 | 75.7  |     48.8      |     25.7      |      31.4       |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q5_0**   | 90.9 | 86.0 | 88.9 | 74.9  |     48.4      |     23.6      |      30.7       |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q4_K_M** | 89.6 | 85.4 | 89.4 | 75.9  |     48.9      |     24.3      |      29.9       |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q4_0**   | 89.6 | 85.4 | 90.2 | 77.8  |     48.2      |     25.7      |      32.6       |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q3_K_M** | 91.5 | 86.6 | 90.7 | 76.7  |     48.3      |     23.6      |      32.0       |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q2_K**   | 92.7 | 84.8 | 87.3 | 74.3  |     47.6      |     23.0      |      28.5       |



### Multiple Programming Languages

|                                            | Python | Java | C++  |  C#  |  TS  |  JS  | PHP  | Bash | Avg. |
|--------------------------------------------|:------:|:----:|:----:|:----:|:----:|:----:|:----:|:----:|:----:|
| **Qwen2.5-Coder-32B-Instruct**             |  92.7  | 80.4 | 79.5 | 82.9 | 86.8 | 85.7 | 78.9 | 48.1 | 79.4 |
| **Qwen2.5-Coder-32B-AWQ**                  |  90.2  | 83.5 | 80.7 | 82.3 | 85.5 | 85.1 | 79.5 | 49.4 | 79.5 |
| **Qwen2.5-Coder-32B-Instruct-GPTQ-Int8**   |  90.9  | 84.2 | 81.4 | 80.4 | 85.5 | 87.6 | 79.5 | 49.4 | 79.8 |
| **Qwen2.5-Coder-32B-Instruct-GPTQ-Int4**   |  92.1  | 83.5 | 82.6 | 80.4 | 84.3 | 86.3 | 78.3 | 50.0 | 79.7 |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q8_0**   |  90.2  | 84.8 | 82.0 | 81.0 | 85.5 | 87.6 | 80.1 | 49.4 | 80.1 |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q6_K**   |  90.9  | 83.5 | 82.0 | 81.6 | 84.9 | 87.0 | 80.7 | 48.7 | 79.9 |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q5_K_M** |  90.2  | 83.5 | 82.6 | 81.0 | 85.5 | 87.0 | 79.5 | 48.7 | 79.8 |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q5_0**   |  90.2  | 84.8 | 82.0 | 81.6 | 85.5 | 87.0 | 80.1 | 48.1 | 79.9 |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q4_K_M** |  90.2  | 84.8 | 81.4 | 82.3 | 85.5 | 86.3 | 80.1 | 50.6 | 80.2 |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q4_0**   |  88.4  | 82.9 | 80.1 | 81.0 | 86.8 | 85.7 | 78.3 | 48.1 | 78.9 |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q3_K_M** |  90.9  | 84.2 | 85.1 | 82.3 | 84.9 | 87.0 | 80.1 | 49.4 | 80.5 |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q2_K**   |  90.2  | 81.0 | 82.6 | 81.6 | 83.6 | 84.5 | 80.1 | 48.7 | 79.1 |



### Code Editing & Code Reasoning & SQL

|                                            | Aider (whole) | Aider (diff) | CRUXEval-Input-CoT | CRUXEval-Output-CoT | Spider | Bird |
|--------------------------------------------|:-------------:|:------------:|:------------------:|:-------------------:|:------:|:----:|
| **Qwen2.5-Coder-32B-Instruct**             |     73.7      |     71.4     |        75.2        |        83.4         |  85.1  | 58.4 |
| **Qwen2.5-Coder-32B-AWQ**                  |     73.7      |     67.7     |        75.1        |        83.1         |  83.6  | 57.3 |
| **Qwen2.5-Coder-32B-Instruct-GPTQ-Int8**   |     74.4      |     73.7     |        75.8        |        83.6         |  84.8  | 58.1 |
| **Qwen2.5-Coder-32B-Instruct-GPTQ-Int4**   |     72.2      |     67.7     |        75.8        |        83.5         |  85.0  | 57.6 |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q8_0**   |     72.9      |     69.9     |        80.5        |        83.8         |  84.5  | 57.9 |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q6_K**   |     72.9      |     73.7     |        78.1        |        83.5         |  84.7  | 58.1 |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q5_K_M** |     74.4      |     69.9     |        78.4        |        84.6         |  85.3  | 57.7 |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q5_0**   |     71.4      |     72.2     |        80.6        |        83.2         |  84.9  | 57.4 |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q4_K_M** |     75.2      |     69.2     |        79.0        |        83.5         |  84.5  | 57.5 |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q4_0**   |     74.4      |     71.4     |        78.5        |        84.0         |  84.7  | 57.2 |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q3_K_M** |     72.9      |     68.4     |        78.8        |        83.9         |  84.4  | 57.4 |
| **Qwen2.5-Coder-32B-Instruct-GGUF-Q2_K**   |     69.9      |     61.7     |        75.5        |        81.1         |  83.4  | 56.1 |

