# Fill-In-the-Middle(FIM) benchmarks
## CrossCodeEval
* 数据准备
```bash
cd cceval
bash bash prepare_data.sh
```
* 使用方法
```bash
bash ./run_cceval.sh <模型路径> <输出目录> <tp>
```
* 参数说明
- `<模型路径>`: 预训练模型的路径
- `<输出目录>`: 评测结果的保存目录
- `<tp>`: 并行gpu数量

* 是否使用cross-file context
脚本支持两种上下文模式，通过`model_type`参数控制：
- `codelm_right_cfc_left`: 启用跨文件上下文模式
- `codelm_leftright_context`: 禁用跨文件上下文模式

* 主要参数
- `cfc_seq_length`: 跨文件上下文的最大长度（默认：2048）
- `right_context_length`: 右侧上下文的最大长度（默认：2048）
- `gen_length`: 代码补全生成的长度（默认：50）
- `max_seq_length`: 总序列最大长度（默认：8192）

## CrossCodeLongEval
* 数据准备
```bash
cd cclongeval
bash bash prepare_data.sh
```
* 使用方法
```bash
bash ./run_cclongeval.sh <模型路径> <输出目录> <tp>
```

## RepoEval
* 使用方法
```bash
bash ./run_repoeval.sh <模型路径> <输出目录> <tp>
```

## humaneval-infiiling
* 使用方法
```bash
bash ./run_hm_fim.sh <模型路径> <输出目录> <tp>
```

## 环境说明
*tree-sitter == 0.20.1*