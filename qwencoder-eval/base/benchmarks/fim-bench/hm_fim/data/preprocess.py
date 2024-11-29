import pandas as pd
import json


def parquet_to_jsonl(parquet_file_path, jsonl_file_path):
    # 读取parquet文件
    df = pd.read_parquet(parquet_file_path)

    # 打开一个新的jsonl文件
    with open(jsonl_file_path, "w", encoding="utf-8") as f:
        # 遍历DataFrame的每一行
        for index, row in df.iterrows():
            # 将行转换为字典，然后转换为json字符串
            json_str = json.dumps(row.to_dict(), ensure_ascii=False)
            # 写入到jsonl文件中
            f.write(json_str + "\n")


if __name__ == "__main__":
    parquet_to_jsonl("./train.parquet", "./fim_singline.jsonl")
