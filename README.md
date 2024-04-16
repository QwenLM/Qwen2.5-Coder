# CodeQwen1.5

<p align="center">
    <img src="https://qianwen-res.oss-accelerate-overseas.aliyuncs.com/assets/blog/codeqwen1.5/codeqwen_logo_final.png" width="400"/>
<p>

<p align="center">
        🤗 <a href="https://huggingface.co/Qwen/CodeQwen1.5-7B-Chat">Hugging Face</a>&nbsp&nbsp | &nbsp&nbsp🤖 <a href="https://modelscope.cn/organization/qwen">ModelScope</a>&nbsp&nbsp | &nbsp&nbsp 📑 <a href="https://qwenlm.github.io">Blog</a> &nbsp&nbsp ｜ &nbsp&nbsp📖 <a href="https://qwen.readthedocs.io/">Documentation</a>
<br>
🖥️ <a href="https://huggingface.co/spaces/Qwen/Qwen1.5-72B-Chat">Demo</a>&nbsp&nbsp | &nbsp&nbsp💬 <a href="https://github.com/QwenLM/Qwen/blob/main/assets/wechat.png">WeChat (微信)</a>&nbsp&nbsp | &nbsp&nbsp🫨 <a href="https://discord.gg/CV4E9rpNSD">Discord</a>&nbsp&nbsp
</p>


Visit our Hugging Face or ModelScope organization (click links above), search checkpoints with names starting with `CodeQwen1.5-`, and you will find all you need! Enjoy!

## Introduction

CodeQwen1.5 is the Code-Specific version of Qwen1.5. It is a transformer-based decoder-only language model pretrained on a large amount of data of codes.

1. Strong code generation capabilities and competitve performance across a series of benchmarks;
2. Supporting long context understanding and generation with the context length of 64K tokens;
3. Supporting 92 coding languages;
```
['ada', 'agda', 'alloy', 'antlr', 'applescript', 'assembly', 'augeas', 'awk', 'batchfile', 'bluespec', 'c', 'c#', 'c++', 'clojure', 'cmake', 'coffeescript', 'common-lisp', 'css', 'cuda', 'dart', 'dockerfile', 'elixir', 'elm', 'emacs-lisp', 'erlang', 'f#', 'fortran', 'glsl', 'go', 'groovy', 'haskell', 'html', 'idris', 'isabelle', 'java', 'java-server-pages', 'javascript', 'json', 'julia', 'jupyter-notebook', 'kotlin', 'lean', 'literate-agda', 'literate-coffeescript', 'literate-haskell', 'lua', 'makefile', 'maple', 'markdown', 'mathematica', 'matlab', 'objectc++', 'ocaml', 'pascal', 'perl', 'php', 'powershell', 'prolog', 'protocol-buffer', 'python', 'r', 'racket', 'restructuredtext', 'rmarkdown', 'ruby', 'rust', 'sas', 'scala', 'scheme', 'shell', 'smalltalk', 'solidity', 'sparql', 'sql', 'stan', 'standard-ml', 'stata', 'swift', 'systemverilog', 'tcl', 'tcsh', 'tex', 'thrift', 'typescript', 'verilog', 'vhdl', 'visual-basic', 'vue', 'xslt', 'yacc', 'yaml', 'zig']
```
4. Excellent performance in text-to-SQL, bug fix, etc.

Detailed performance and introduction are shown in this <a href="https://qwenlm.github.io/blog/codeqwen1.5"> 📑 blog</a>.

## Performance

### EvalPlus 

<table style="text-align:center;">
    <tr style="font-weight:bold">
        <td style="text-align: left">Model</td>
        <td style="text-align: left">Size</td>
        <td>
            <div>HumanEval</div>
            <div class="cell-aux">0-shot</div>
        </td>
        <td>
            <div>HumanEval+</div>
            <div class="cell-aux">0-shot</div>
        </td>
        <td>
            <div>MBPP</div>
            <div class="cell-aux">0-shot</div>
        </td>
        <td>
            <div>MBPP+</div>
            <div class="cell-aux">0-shot</div>
        </td>
        <td>
            <div>MBPP</div>
            <div class="cell-aux">3-shot</div>
        </td>
    </tr>
    <tr>
        <td colspan=7><center><b>Base Model</b></center></td>
    </tr>
    <tr>
        <td style="text-align: left">CodeLlama-Base</td>
        <td style="text-align: left">7B</td>
        <td>33.5</td>
        <td>25.6</td>
        <td>52.1</td>
        <td>41.6</td>
        <td>38.6</td>
    </tr>
    <tr>
        <td style="text-align: left">StarCoder2</td>
        <td style="text-align: left">7B</td>
        <td>35.4</td>
        <td>29.9</td>
        <td>54.4</td>
        <td>45.6</td>
        <td>51.0</td>
    </tr>
    <tr>
        <td style="text-align: left">DeepSeek-Coder-Base</td>
        <td style="text-align: left">6.7B</td>
        <td>47.6</td>
        <td>39.6</td>
        <td>70.2</td>
        <td>56.6</td>
        <td>60.6</td>
    </tr>
    <tr>
        <td style="text-align: left"><b>CodeQwen1.5</b></td>
        <td style="text-align: left">7B</td>
        <td>51.8</td>
        <td>45.7</td>
        <td>72.2</td>
        <td>60.2</td>
        <td>61.8</td>
    </tr>
    <tr>
        <td colspan=7><center><b>Chat Model</b></center></td>
    </tr>
    <tr>
        <td style="text-align: left">GPT-3.5-Turbo</td>
        <td style="text-align: left">-</td>
        <td>76.8</td>
        <td>70.7</td>
        <td>82.5</td>
        <td>69.7</td>
        <td>70.8</td>
    </tr>
    <tr>
        <td style="text-align: left">GPT-4-Turbo (Nov 2023)</td>
        <td style="text-align: left">-</td>
        <td>85.4</td>
        <td>81.7</td>
        <td>83.5</td>
        <td>70.7</td>
        <td>80.0</td>
    </tr>
    <tr>
        <td style="text-align: left">DeepSeek-Coder-Instruct</td>
        <td style="text-align: left">6.7B</td>
        <td>73.8</td>
        <td>70.1</td>
        <td>73.2</td>
        <td>63.4</td>
        <td>65.4</td>
    </tr>
    <tr>
        <td style="text-align: left"><b>CodeQwen1.5-Chat</b></td>
        <td style="text-align: left">7B</td>
        <td>83.5</td>
        <td>78.7</td>
        <td>77.7</td>
        <td>67.2</td>
        <td>70.6</td>
    </tr>
</table>

### LiveCodeBench

<table style="text-align:center">
    <tr style="font-weight:bold">
        <td style="text-align: left">Model</td>
        <td style="text-align: left">Size</td>
        <td>
            <div>Code Generation</div>
            <div class="cell-aux">
                <div>All Time</div>
                <div>Pass@1</div>
            </div>
        </td>
        <td>
            <div>Code Generation</div>
            <div class="cell-aux">
                <div>2023/9/1 ~ 2024/4/1</div>
                <div>Pass@1</div>
            </div>
        </td>
    </tr>
    <tr>
        <td colspan=4><center><b>Base Model</b></center></td>
    </tr>
    <tr>
        <td style="text-align: left">CodeLlama-Base</td>
        <td style="text-align: left">7B</td>
        <td>6.5</td>
        <td>7.6</td>
    </tr>
    <tr>
        <td style="text-align: left">StarCoder2</td>
        <td style="text-align: left">7B</td>
        <td>11.3</td>
        <td>12.7</td>
    </tr>
    <tr>
        <td style="text-align: left">DeepSeek-Coder-Base</td>
        <td style="text-align: left">6.7B</td>
        <td>19.1</td>
        <td>13.7</td>
    </tr>
    <tr>
        <td style="text-align: left"><b>CodeQwen1.5</b></td>
        <td style="text-align: left">7B</td>
        <td><b>21.8</b></td>
        <td><b>19.3</b></td>
    </tr>
    <tr>
        <td colspan=4><center><b>Chat Model</b></center></td>
    </tr>
    <tr>
        <td style="text-align: left">CodeLlama-Instruct</td>
        <td style="text-align: left">7B</td>
        <td>10.6</td>
        <td>12.4</td>
    </tr>
    <tr>
        <td style="text-align: left">DeepSeek-Coder-Instruct</td>
        <td style="text-align: left">6.7B</td>
        <td>21.6</td>
        <td>19.2</td>
    </tr>
    <tr>
        <td style="text-align: left"><b>CodeQwen1.5-Chat</b></td>
        <td style="text-align: left">7B</td>
        <td><b>25.0</b></td>
        <td><b>23.2</b></td>
    </tr>
</table>

### Text-to-SQL

<table style="text-align:center">
    <tr style="font-weight:bold">
        <td style="text-align: left">Model</td>
        <td style="text-align: left">Size</td>
        <td>
            <div>Spider</div>
            <div class="cell-aux">
                <div>Execution Accuracy</div>
                <div>Dev Set</div>
            </div>
        </td>
        <td>
            <div>Bird</div>
            <div class="cell-aux">
                <div>Execution Accuracy</div>
                <div>Dev Set</div>
            </div>
        </td>
    </tr>
    <tr>
        <td style="text-align: left">GPT-3.5-Turbo</td>
        <td style="text-align: left">-</td>
        <td>70.1</td>
        <td>37.2</td>
    </tr>
    <tr>
        <td style="text-align: left">GPT-4</td>
        <td style="text-align: left">-</td>
        <td>85.3</td>
        <td>50.7</td>
    </tr>
    <tr>
        <td style="text-align: left">CodeLlama-Instruct</td>
        <td style="text-align: left">7B</td>
        <td>59.5</td>
        <td>22.4</td>
    </tr>
    <tr>
        <td style="text-align: left">DeepSeek-Coder-Instruct</td>
        <td style="text-align: left">6.7B</td>
        <td>70.1</td>
        <td>39.4</td>
    </tr>
    <tr>
        <td style="text-align: left"><b>CodeQwen1.5-Chat</b></td>
        <td style="text-align: left">7B</td>
        <td><b>77.9</b></td>
        <td><b>42.0</b></td>
    </tr>
</table>

## Requirements
* `transformers>=4.37.0` for Qwen1.5 dense models.

> [!Warning]
> <div align="center">
> <b>
> 🚨 This is a must because `transformers` integrated Qwen2 codes since `4.37.0`.
> </b>
> </div>


## Citation
If you find our work helpful, feel free to give us a cite.

```
@article{qwen,
  title={Qwen Technical Report},
  author={Jinze Bai and Shuai Bai and Yunfei Chu and Zeyu Cui and Kai Dang and Xiaodong Deng and Yang Fan and Wenbin Ge and Yu Han and Fei Huang and Binyuan Hui and Luo Ji and Mei Li and Junyang Lin and Runji Lin and Dayiheng Liu and Gao Liu and Chengqiang Lu and Keming Lu and Jianxin Ma and Rui Men and Xingzhang Ren and Xuancheng Ren and Chuanqi Tan and Sinan Tan and Jianhong Tu and Peng Wang and Shijie Wang and Wei Wang and Shengguang Wu and Benfeng Xu and Jin Xu and An Yang and Hao Yang and Jian Yang and Shusheng Yang and Yang Yao and Bowen Yu and Hongyi Yuan and Zheng Yuan and Jianwei Zhang and Xingxuan Zhang and Yichang Zhang and Zhenru Zhang and Chang Zhou and Jingren Zhou and Xiaohuan Zhou and Tianhang Zhu},
  journal={arXiv preprint arXiv:2309.16609},
  year={2023}
}
```

## Contact Us
If you are interested to leave a message to either our research team or product team, join our [Discord](https://discord.gg/z3GAxXZ9Ce) or [WeChat groups](https://github.com/QwenLM/Qwen/blob/main/assets/wechat.png)!
