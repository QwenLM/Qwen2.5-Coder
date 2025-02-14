REPO_DIR="./repos"
REPO_NAME="PTable"
export PATH=./envs/repo_${REPO_NAME}/bin:$PATH
cd ${REPO_DIR}/${REPO_NAME};
pip install -r requirements.txt
pip install pytest pytest-cov pytest-benchmark coincidence cssutils docutils openpyxl hypothesis pycodestyle
echo "repo_${REPO_NAME}: ${REPO_DIR}/repo_${REPO_NAME}"
python evaluate_repo.py
