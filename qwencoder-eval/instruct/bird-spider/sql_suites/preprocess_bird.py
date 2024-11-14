import json
import shutil
from tqdm import tqdm

from utils import save_json, save_lines, load_json, load_lines, join_seperator, extract_create_table_prompt
from pathlib import Path


SCHEMA_EXAMPLE_ROWS = 0


def create_codex_prompt(e, db_root, with_knowledge):
    db_id = e["db_id"]
    db_path = Path(db_root) / db_id / f"{db_id}.sqlite"
    prompt = extract_create_table_prompt(db_path, limit_value=SCHEMA_EXAMPLE_ROWS)

    if with_knowledge:
        prompt += f"-- External Knowledge: {e['evidence']}\n\n"
        prompt += "-- Using valid SQLite and understanding External Knowledge, answer the following questions for the tables provided above.\n\n"
    else:
        prompt += "-- Using valid SQLite, answer the following questions for the tables provided above.\n"

    prompt += f"Question: {e['question']}\n"

    return prompt


def process_data(questions, db_root, with_knowledge):
    processed = []
    for e in tqdm(questions):
        item = {
            "id": len(processed),
            "db_id": e["db_id"],
            "instruction": create_codex_prompt(e, db_root, with_knowledge=with_knowledge),
            "output": e["SQL"],
        }
        processed.append(item)

    return processed


if __name__ == "__main__":
    #
    # 1. copy databases
    # 2. build `CREATE and Question` style dataset
    #
    # -> data/bird-dev
    #    - database/
    #    - bird-dev.json (SELECT_ROW=0)
    #      - id
    #      - db_id
    #      - instruction
    #      - output
    #    - golden.sql
    #
    # There's no re-order.
    #
    output_root = Path("data/bird-dev")
    output_root.mkdir(exist_ok=True, parents=True)

    bird_raw_folder = Path("data_raw/bird")
    bird_dev_questions = load_json(bird_raw_folder / "dev.json")
    bird_databases = bird_raw_folder / "dev_databases"

    bird_dev_questions_processed = process_data(bird_dev_questions, bird_databases, with_knowledge=True)
    save_json(bird_dev_questions_processed, output_root / "bird-dev.json")

    bird_dev_questions_nokg_processed = process_data(bird_dev_questions, bird_databases, with_knowledge=False)
    save_json(bird_dev_questions_nokg_processed, output_root / "bird-dev-nokg.json")

    bird_dev_golden = [join_seperator(e["output"], e["db_id"]) for e in bird_dev_questions_processed]
    save_lines(bird_dev_golden, output_root / "golden.sql")

    bird_used_databases = output_root / "database"
    bird_used_databases.mkdir(parents=True, exist_ok=True)
    db_ids = set([e["db_id"] for e in bird_dev_questions_processed])

    for db_id in db_ids:
        raw_db_folder = bird_databases / db_id
        db_folder = bird_used_databases / db_id
        if db_folder.exists() and db_folder.is_dir():
            print(f"Skip already done: {db_id}")
        else:
            shutil.copytree(raw_db_folder, db_folder)
            print(f"Copied {db_id} from `{raw_db_folder}` to `{db_folder}`")
