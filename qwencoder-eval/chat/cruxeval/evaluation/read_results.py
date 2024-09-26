# Copyright (c) Meta Platforms, Inc. and affiliates.

from tabulate import tabulate
import json
import os
import glob

current_dir = os.path.join(os.getcwd(), "evaluation_results")
json_files = glob.glob(os.path.join(current_dir, '*.json'))

accs = {}
models = []
for file in json_files:
    f = json.load(open(os.path.join("evaluation_results", file), "r"))
    model_name = file.split("_temp")[0].split("results/")[1].strip()
    temperature = float(file.split(".json")[0].split("_temp")[1].split("_")[0])
    mode = file.split(".json")[0].split("_")[-1]
    models.append(model_name)

    if temperature == 0.2:
        accs[(mode, model_name, temperature)] = round(f["pass_at_1"], 1)
    else:
        accs[(mode, model_name, temperature)] = round(f["pass_at_5"], 1)

models = list(set(models))
models.sort()


for i in ["input", "output"]:
    data = []
    for m in models:
        model = m
        # model = m.split(" ")[0].split("/")[1]
        try: pass_at_1 = accs[(i, m, 0.2)]
        except: pass_at_1 = "n/a"
        try: pass_at_5 = accs[(i, m, 0.8)]
        except: pass_at_5 = "n/a"
        try: data.append([model, pass_at_1, pass_at_5])
        except: pass
    
    headers = ["Model", "Pass@1", "Pass@5"]
    data.sort(key = lambda x:x[1])
    table = tabulate(data, headers=headers, tablefmt="pipe")
    print(f"********* CRUXEval-{i.capitalize()} *********\n")
    print(table)
    print("\n")