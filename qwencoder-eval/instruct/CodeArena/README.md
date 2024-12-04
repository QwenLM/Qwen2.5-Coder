## Dataset Summary
To bridge the gap between the model-generated response and human preference, we present a rigorous human-curated benchmark CodeArena to emulate the complexity and diversity of real-world coding tasks, where 397 high-quality samples spanning 40 categories and 40 languages, carefully curated from user queries.

## Download Dataset
```sh
git lfs install
git clone https://huggingface.co/datasets/CSJianYang/CodeArena
```

## Evaluation
```sh
cd ./code_arena;
MODEL_DIR="Qwen2.5-Coder-32B"
INPUT_PATH="./data/CodeArena_v1.jsonl"
OUTPUT_PATH="./Qwen2.5-Coder-32B/results.jsonl"
TP=1
MAX_LEN=16384
CHAT_TEMPLATE="auto"
bash eval_arena.sh ${INPUT_PATH} ${OUTPUT_PATH} ${MODEL_DIR} ${TP} ${MAX_LEN} ${CHAT_TEMPLATE}
```

## Data Example
An example of 'validation' looks as follows:
```
{
    "id": "60670a8d9b1e39dd845fb1639d0d8b86",
    "messages": "[{'role': 'user', 'content': 'move gradient chart to the right side\n\n  <CardContent>\n                <Typography color="textSecondary" gutterBottom>\n                  Average Sentiment\n                </Typography>\n                  <Box display="flex" alignItems="flex-end">\n                    <NegativeIcon\n                      style={{ marginRight: "10px", color: "red" }}\n                    />\n                    <Box textAlign="center">\n                      <Typography variant="h5">\n                        {workspaceConversationsDashboardStats.averageSentiment.toFixed(\n                          2\n                        )}\n                      </Typography>\n                      <GaugeContainer\n                        width={100}\n                        height={100}\n                        innerRadius={25} // Adjust for smaller gauge\n                        startAngle={-110}\n                        endAngle={110}\n                        value={\n                          (workspaceConversationsDashboardStats.averageSentiment +\n                            1) *\n                          50\n                        }\n                      >\n                        <GaugeReferenceArc\n                          style={{ stroke: "url(#gradient)", strokeWidth: 3 }} // Adjust stroke width\n                        />\n                        <defs>\n                          <linearGradient\n                            id="gradient"\n                            x1="0%"\n                            y1="0%"\n                            x2="100%"\n                            y2="0%"\n                          >\n                            <stop\n                              offset="0%"\n                              style={{ stopColor: "red", stopOpacity: 1 }}\n                            />\n                            <stop\n                              offset="100%"\n                              style={{ stopColor: "green", stopOpacity: 1 }}\n                            />\n                          </linearGradient>\n                        </defs>\n                        <GaugePointer />\n                      </GaugeContainer>\n                    </Box>\n                    <PositiveIcon\n                      style={{ marginLeft: "10px", color: "green" }}\n                    />\n                  </Box>\n              </CardContent>'}]",
    "gpt-4-turbo-2024-04-09_response": "<CardContent>\n  <Typography color="textSecondary" gutterBottom>\n    Average Sentiment\n  </Typography>\n  <Box display="flex" alignItems="flex-end" justifyContent="flex-end">\n    <NegativeIcon\n      style={{ marginRight: "10px", color: "red" }}\n    />\n    <Box textAlign="center">\n      <Typography variant="h5">\n        {workspaceConversationsDashboardStats.averageSentiment.toFixed(\n          2\n        )}\n      </Typography>\n      <GaugeContainer\n        width={100}\n        height={100}\n        innerRadius={25} // Adjust for smaller gauge\n        startAngle={-110}\n        endAngle={110}\n        value={\n          (workspaceConversationsDashboardStats.averageSentiment +\n            1) *\n          50\n        }\n      >\n        <GaugeReferenceArc\n          style={{ stroke: "url(#gradient)", strokeWidth: 3 }} // Adjust stroke width\n        />\n        <defs>\n          <linearGradient\n            id="gradient"\n            x1="0%"\n            y1="0%"\n            x2="100%"\n            y2="0%"\n          >\n            <stop\n              offset="0%"\n              style={{ stopColor: "red", stopOpacity: 1 }}\n            />\n            <stop\n              offset="100%"\n              style={{ stopColor: "green", stopOpacity: 1 }}\n            />\n          </linearGradient>\n        </defs>\n        <GaugePointer />\n      </GaugeContainer>\n    </Box>\n    <PositiveIcon\n      style={{ marginLeft: "10px", color: "green" }}\n    />\n  </Box>\n</CardContent>",
    "difficulty": "easy",
    "programming_language": ['JavaScript'],
}
```
## Citation
If you use the data from this project, please cite the original paper:
```

```
