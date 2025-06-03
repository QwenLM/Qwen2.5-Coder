import json
import torch
import random
import os
from torch.utils.data import IterableDataset, Dataset
from typing import Dict, Optional, Sequence
import transformers
import logging
import numpy as np
from utils import utils
logging.basicConfig(level=logging.DEBUG)  
class SupervisedDataset(Dataset):
    """Dataset for supervised fine-tuning."""

    def __init__(self, data_path: str, tokenizer: transformers.PreTrainedTokenizer, args):
        super(SupervisedDataset, self).__init__()
        logging.warning("Loading data...")
        if data_path.endswith(".npy"):
            self.input_ids = np.load(data_path, allow_pickle=True)
        else:
            self.input_ids = utils.read_jsonl_file(data_path)
        original_data_num = len(self.input_ids)
        logging.info("Completely Loading tokenized sentences...")
        def truncate(sentence):
            return torch.tensor(sentence[:args.model_max_length] + [tokenizer.eos_token_id] if len(sentence) > args.model_max_length else sentence, dtype=torch.long)
        if args.truncate_source:
            self.labels = [truncate(example["label"]) for example in self.input_ids]
            self.input_ids = [truncate(example["input_ids"]) for example in self.input_ids]
        else:
            self.labels = [torch.tensor(example["label"], dtype=torch.long) for example in self.input_ids if len(example["input_ids"]) < args.model_max_length]
            self.input_ids = [torch.tensor(example["input_ids"], dtype=torch.long) for example in self.input_ids if len(example["input_ids"]) < args.model_max_length]
        print(f"Samples: {original_data_num} -> {len(self.input_ids)}")


    def __len__(self):
        return len(self.input_ids)

    def __getitem__(self, i) -> Dict[str, torch.Tensor]:        
        return dict(input_ids=self.input_ids[i], labels=self.labels[i])


class MMAPSupervisedDataset(Dataset):
    """Dataset for supervised fine-tuning."""
    def __init__(self, data_path: str, tokenizer: transformers.PreTrainedTokenizer, args):
        super(Dataset, self).__init__()
        logging.warning("Loading data...")
        input_ids_path = data_path
        labels_path = data_path.replace(".input_ids.mmap", ".labels.mmap")
        lengths_path = data_path.replace(".input_ids.mmap", ".lengths.mmap")
        input_ids_shape_path = input_ids_path + ".shape.json"
        labels_shape_path = labels_path + ".shape.json"
        lengths_shape_path = lengths_path + ".shape.json"
        self.model_max_length = args.model_max_length
        self.truncate_source = args.truncate_source
        with open(input_ids_shape_path, 'r') as f:
            input_ids_shape_info = json.load(f)
        with open(labels_shape_path, 'r') as f:
            labels_shape_info = json.load(f)
        with open(lengths_shape_path, 'r') as f:
            lengths_shape_info = json.load(f)
        self.input_ids = np.memmap(
            input_ids_path,
            dtype=np.int32,
            mode='r',
            shape=(input_ids_shape_info['n_samples'], input_ids_shape_info['max_len'])
        )
        self.labels = np.memmap(
            labels_path, 
            dtype=np.int32,
            mode='r',
            shape=(labels_shape_info['n_samples'], labels_shape_info['max_len'])
        )
        self.lengths = np.memmap(
            lengths_path, 
            dtype=np.int32,
            mode='r',
            shape=(lengths_shape_info['n_samples'], lengths_shape_info['max_len'])
        )
        logging.info(f"Loaded {len(self.input_ids)} samples using mmap")

    def __len__(self):
        return len(self.input_ids)

    def __getitem__(self, i) -> Dict[str, torch.Tensor]:     
        length = int(self.lengths[i])
        input_ids = self.input_ids[i][:length]
        labels = self.labels[i][:length]
        input_ids = torch.tensor(input_ids, dtype=torch.long)
        labels = torch.tensor(labels, dtype=torch.long)
        if self.truncate_source:
            input_ids = input_ids[:self.model_max_length]
            labels = labels[:self.model_max_length]
        return dict(input_ids=input_ids, labels=labels)

class BufferedJsonlDataset(IterableDataset):
    def __init__(
        self,
        data_path: str,
        buffer_size: int = 1000,  # 缓冲区大小
        seed: Optional[int] = None,
        shuffle: bool = True
    ):
        super().__init__()
        self.data_path = data_path
        self.buffer_size = buffer_size
        self.shuffle = shuffle
        self.seed = seed
        self.file_size = os.path.getsize(data_path)
        logging.info(f"Reading from {data_path}: {len(self.file_size)}")
    

    def __iter__(self):
        worker_info = torch.utils.data.get_worker_info()
        if self.seed is not None:
            random_seed = self.seed
            if worker_info is not None:
                random_seed += worker_info.id
            np.random.seed(random_seed)
        start_pos = np.random.randint(0, self.file_size) if self.shuffle else 0      
        buffer = []
        with open(self.data_path, 'r', encoding='utf-8') as f:
            while True:
                if not buffer:
                    f.seek(start_pos)
                    partial_line = f.readline()
                    if not partial_line:  # 如果到达文件末尾，从头开始
                        f.seek(0)
                        partial_line = f.readline()
                    buffer = []
                    for _ in range(self.buffer_size):
                        line = f.readline()
                        if not line:  
                            f.seek(0)
                            line = f.readline()
                        try:
                            data = json.loads(line.strip())
                            if "input_ids" in data:
                                buffer.append(data["input_ids"])
                        except json.JSONDecodeError:
                            logging.info("Invalid json line")
                            continue
                    if self.shuffle:
                        random.shuffle(buffer)
                if buffer:
                    yield buffer.pop()
                else:
                    break

    def __len__(self):
        return self.file_size

class JSONLDataset(IterableDataset):
    def __init__(self, data_path, buffer_size=1000):
        """
        Args:
            data_path: jsonl文件路径
            buffer_size: 缓存大小
        """
        super().__init__()
        self.data_path = data_path
        self.buffer_size = buffer_size
        self.file_size = os.path.getsize(data_path)
    
    def get_random_start_pos(self, mm):
        """获取随机起始位置"""
        # 随机选择一个文件位置
        pos = random.randint(0, self.file_size - 1)
        
        # 调整到最近的行首
        while pos > 0 and mm[pos-1] != ord('\n'):
            pos -= 1
        return pos

    def read_lines(self, mm, start_pos):
        """从指定位置读取数据"""
        buffer = []
        current_pos = start_pos
        
        while len(buffer) < self.buffer_size and current_pos < self.file_size:
            line_start = current_pos
            
            # 找到行尾
            while current_pos < self.file_size and mm[current_pos] != ord('\n'):
                current_pos += 1
            
            if current_pos < self.file_size:
                line = mm[line_start:current_pos].decode('utf-8')
                try:
                    data = json.loads(line)
                    if "input_ids" in data:
                        buffer.append(data["input_ids"])
                except json.JSONDecodeError:
                    pass  # 跳过无效的JSON行
                
                current_pos += 1  # 跳过换行符
        
        return buffer, current_pos

    def __iter__(self):
        worker_info = torch.utils.data.get_worker_info()
        with open(self.data_path, 'rb') as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            if worker_info is not None:
                start_pos = self.get_random_start_pos(mm)
            else:
                start_pos = 0
            current_pos = start_pos
            while True:
                buffer, next_pos = self.read_lines(mm, current_pos)
                if not buffer and next_pos >= self.file_size:
                    current_pos = 0
                    continue
                elif not buffer:
                    current_pos = next_pos
                    continue
                random.shuffle(buffer)
                for item in buffer:
                    yield torch.tensor(item)
                
                current_pos = next_pos

    def __len__(self):
        return int(self.file_size / 100)  # 假设每行平均100字节


if __name__ == "__main__":
    from torch.utils.data import DataLoader
    dataset = BufferedJsonlDataset(
        data_path="path/to/your/large.jsonl",
        buffer_size=1000,
        seed=42,
        shuffle=True
    )
    dataloader = DataLoader(
        dataset,
        batch_size=32,
        num_workers=4, 
        pin_memory=True 
    )
    for batch in dataloader:
        pass
