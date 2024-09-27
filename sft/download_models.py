from modelscope.hub.snapshot_download import snapshot_download
model_dir = snapshot_download('Qwen/Qwen2.5-Coder-1.5B', cache_dir='./pretrained_models/')
model_dir = snapshot_download('Qwen/Qwen2.5-Coder-7B', cache_dir='./pretrained_models/')