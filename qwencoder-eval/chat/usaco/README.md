# Can Language Models Solve Olympiad Programming?

This repo holds the code and demos for "Can Language Models Solve Olympiad Programming?" by Quan Shi, Michael Tang, Karthik Narasimhan, and Shunyu Yao. [Paper Link](https://arxiv.org/abs/2404.10952v1)

![memory_retrieval](https://github.com/princeton-nlp/USACO/assets/78577924/e225d8a3-ca88-46bf-88d1-ced17241a4fa)

## Setup

Run
```
git clone https://github.com/princeton-nlp/USACO
cd USACO
pip install -r requirements.txt
```

See download links and details about data in the Data section below.

## OpenAI API key

Run
`echo OPENAI_API_KEY=[YOUR_KEY] >> .env`.

In the code, we read this via
```
from dotenv import load_dotenv
load_dotenv()
```
and seems less buggy than `export OPENAI_API_KEY`.

## Judge sandbox directories

Local evaluation requires absolute paths — please update the global path constants at the top of the files `USACOBench/evaluation/judges/usaco_judge.py`, `USACOBench/evaluation/judges/usaco_batch_judge.py`, `USACOBench/tools/sandbox.py`, and `USACOBench/evaluation/judges/usaco_utils.py`. A good default is to set them to `{parent of this repository}/USACO/{copy rest of path}`.

Note that as more solutions are generated, the directory may become large. Optionally to save space, you may also delete solutions or pickle files you no longer want at any time, as long as judging is not currently running.

## Data

USACO-related data (problems and problem dict) and the `cp_handbook` corpus can be downloaded [here](https://drive.google.com/file/d/1z5ODOJMqyer1QxzYtEUZ2hbAx-7nU8Vi/view?usp=share_link). Data files are large!

Alternatively, to directly load data folder, run the following on the command line
```
wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=1z5ODOJMqyer1QxzYtEUZ2hbAx-7nU8Vi' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=1z5ODOJMqyer1QxzYtEUZ2hbAx-7nU8Vi" -O data.zip && rm -rf /tmp/cookies.txt
```

Below are descriptions of the contents within the folder:

* `data/corpuses/`: corpuses of competitive programming articles and book chapters (json)
    * `cpbook_v2`: [cp-algorithms book](https://cp-algorithms.com/), split into 157 articles. We currently just use `article` (raw text with problems section removed) for retrieval, but we also provide keys `title` and `full_article` (problems section included) in the corpus.
    * `cp_handbook`: [CP Handbook](https://github.com/pllk/cphb), split into 118 LaTeX sections. We currently use `section_content` for retrieval, but also provide keys `section_title`, `chapter_title`, `chapter_path` (path in the source repo).
* `data/datasets/`: datasets of competitive programming problems (HuggingFace datasets)
    * `usaco_v2`: 484 USACO problems (all available problems with test cases up to September 2023)
    * `usaco307`: 307 USACO problems with python solutions, set utilized in paper


## USACO eval

We evaluate Python locally using `exec`; the execution code is adapted from OpenAI's [HumanEval](https://github.com/openai/human-eval/blob/master/human_eval/execution.py) task -- note that it is important to **take care when running unverified model-generated code**.

To evaluate default solve on a given a model endpoint (only GPT and Claude API endpoints are automatically supported)
```
python run_usaco.py -m gpt-3.5-turbo
```
To replicate open source models, create a model_fn following formatting in `USACOBench/models/gpts.py`. 


Enabling inference methods in the paper such as Episodic Retrieval, Semantic Retrieval, and Reflexion is as simple as passing in the corresponding flags. For example, to run a combination of Episodic and Semantic Retrieval, run
```
python run_usaco.py -m gpt-3.5-turbo -s -e
```

## Reducing Memory Usage
Result sets are by default quite large, as they include sample inputs and outputs on test cases.
To reduce size of result files, go to the file `USACOBench/evaluation/judges/usaco_utils.py`, and:
1. Uncomment line 162
2. Comment out line 163

