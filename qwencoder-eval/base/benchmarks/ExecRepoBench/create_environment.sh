export PATH=./miniconda3/bin:$PATH
repo_name="markdown-it-py"
conda create -n repo_${repo_name} python=3.9 -y
export PATH=./miniconda3/envs/repo_${repo_name}/bin:$PATH
cd ./repos/${repo_name}
pip install -e .
pip install pytest pytest-cov pytest-benchmark coincidence cssutils
