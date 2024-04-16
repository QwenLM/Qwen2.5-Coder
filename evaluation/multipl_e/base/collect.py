# write by codeqwen-7b-chat

import os
import re
from rich.console import Console
from rich.table import Table

# 设置 rich 控制台
console = Console()

# 获取所有 .log 文件的路径
log_file = "./codeqwen-7b.log"

# 创建表格
table = Table(title="Score Table")
table.add_column("Log File")
table.add_column("python", justify="right")
table.add_column("cpp", justify="right")
table.add_column("java", justify="right")
table.add_column("php", justify="right")
table.add_column("ts", justify="right")
table.add_column("cs", justify="right")
table.add_column("sh", justify="right")
table.add_column("js", justify="right")

with open(os.path.join(log_directory, log_file), "r") as file:
    content = file.read()
    
    # 使用正则表达式找到包含 "score is" 的行
    matches = re.findall(r"(\w+)\s*score is\s*([\d.]+)", content)
    scores = {language.lower(): float(score) * 100 for language, score in matches}
    
    # 将数据添加到表格中
    table.add_row(
        log_file,
        f"{scores.get('python', 0.0):.1f}",
        f"{scores.get('cpp', 0.0):.1f}",
        f"{scores.get('java', 0.0):.1f}",
        f"{scores.get('php', 0.0):.1f}",
        f"{scores.get('ts', 0.0):.1f}",
        f"{scores.get('cs', 0.0):.1f}",
        f"{scores.get('sh', 0.0):.1f}",
        f"{scores.get('js', 0.0):.1f}"
    )

# 打印表格
console.print(table)
