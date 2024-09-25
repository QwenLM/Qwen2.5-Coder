# Evaluation Suites for Qwen2.5-Coder Base Models

This repository provides evaluation scripts and configurations designed to benchmark the performance of the Qwen2.5-Coder base models, specifically for code generation tasks. The evaluations utilize various code-related benchmarks to assess the model’s capabilities across multiple dimensions.

## Setup

Before running the evaluation scripts, ensure that your environment is set up properly. The following steps guide you through the process of creating a conda environment and installing the necessary dependencies.

1. **Create a Conda Environment**  
   Use the following command to create and activate a new environment for the evaluation:

    ```bash
    conda create -p ./conda_envs/bigcodebench_env python=3.8
    conda activate conda_envs/bigcodebench_env
    ```

2. **Install Dependencies**  
   After activating the environment, install all required dependencies by running:

    ```bash
    pip install -r requirements/bigcodebench-eval.txt
    ```

## Evaluation

1. **Model Path Modification**  
   Before running the evaluation script, ensure that the model paths are correctly set. Modify the paths as needed based on your local environment or cloud storage setup.

2. **Run Evaluation**  
   Once the environment is ready and the model paths are configured, run the evaluation suite by executing the following script:

    ```bash
    bash run_evaluate_cq2.5.sh
    ```

   This will initiate the evaluation process across the specified benchmarks.

---

## Acknowledgement

We referred to the evaluation code at each benchmark and appreciate their contribution.
