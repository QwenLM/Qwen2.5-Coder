import json
from pathlib import Path
import sqlite3

SPECIAL_SEPERATOR = "\t----- SQL-EVAL -----\t"


def read_packed_sql(file, db_root):
    sqls, db_files = [], []
    with Path(file).open("r") as f:
        for line in f:
            line = line.rstrip()
            if not line:
                continue
            sql, db_id = line.split(SPECIAL_SEPERATOR)

            sqls.append(sql.strip())
            db_file = Path(db_root).joinpath(db_id).joinpath(f"{db_id}.sqlite").resolve()
            db_files.append(str(db_file))

    print(f"Load {len(sqls)} SQLs from {file}")
    return sqls, db_files


def extract_create_table_prompt(db_path, limit_value=3):
    table_query = "SELECT * FROM sqlite_master WHERE type='table';"
    tables = sqlite3.connect(db_path).cursor().execute(table_query).fetchall()
    prompt = ""
    for table in tables:
        table_name = table[1]
        create_table_statement = table[-1]

        table_info_query = f"PRAGMA table_info(`{table_name}`);"
        # top_k_row_query = f"SELECT * FROM `{table_name}` LIMIT {limit_value};"
        top_k_row_query = f"SELECT * FROM {table_name} LIMIT {limit_value};"
        try:
            headers = [x[1] for x in sqlite3.connect(db_path).cursor().execute(table_info_query).fetchall()]
        except:
            print("Error:")
            print(table_info_query)
            print(top_k_row_query)
            exit(0)

        prompt += create_table_statement + ";\n"
        if limit_value > 0:
            top_k_rows = sqlite3.connect(db_path).cursor().execute(top_k_row_query).fetchall()
            prompt += f"/*\n3 example rows:\n{top_k_row_query}\n{'    '.join(headers)}\n"
            for row in top_k_rows:
                row = [str(x) for x in row]
                row = [x if x is not None else "" for x in row]

                prompt += "    ".join(row) + "\n"
            prompt += "*/\n"
        prompt += "\n"
    return prompt


def join_seperator(sql, db_id, sep=SPECIAL_SEPERATOR):
    return f"{sql.strip()}{sep}{db_id.strip()}"


def load_json(path):
    with Path(path).open("r") as f:
        d = json.load(f)
    print(f"Load from {path}")
    return d


def save_json(d, path):
    with Path(path).open("w") as f:
        json.dump(d, f, indent=2)
    print(f"Save to {path}")


def load_lines(path):
    with Path(path).open("r") as f:
        d = [line.strip() for line in f if line.strip()]
    print(f"Load {len(d)} lines from {path}")
    return d


def save_lines(lines, path):
    with Path(path).open("w") as f:
        for line in lines:
            f.write(f"{line.strip()}\n")
    print(f"Save {len(lines)} lines to {path}")
