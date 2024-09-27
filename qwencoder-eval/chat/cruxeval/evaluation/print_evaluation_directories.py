# Copyright (c) Meta Platforms, Inc. and affiliates.

import os

def get_all_directories(path='.'):
    entries = os.listdir(path)
    directories = [entry for entry in entries if os.path.isdir(os.path.join(path, entry))]
    return directories

base_dir = "../model_generations"
d = get_all_directories(base_dir)
d.sort()
print("input directories")
print("run_names=(")
for i in d: 
    new_dir = os.path.join(base_dir, i)
    files = os.listdir(new_dir)
    new_dir = new_dir.split("generations/")[1]
    if "input" in new_dir:
        print(f"     \"{new_dir}\"")
print(")")

print("\n\noutput directories")
print("run_names=(")
for i in d: 
    new_dir = os.path.join(base_dir, i)
    files = os.listdir(new_dir)
    new_dir = new_dir.split("generations/")[1]
    if "output" in new_dir:
        print(f"    \"{new_dir}\"")
print(")")