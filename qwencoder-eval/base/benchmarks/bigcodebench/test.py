from data import get_bigcodebench
import json

subset = 'hard'
dataset = get_bigcodebench(subset=subset)

save_path = f'bigcodebench_{subset}.json'
with open(save_path, 'w') as f:
    json.dump(dataset, f)