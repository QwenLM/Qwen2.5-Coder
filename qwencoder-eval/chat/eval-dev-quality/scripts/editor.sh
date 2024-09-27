#!/bin/bash

set -exuo pipefail

export VSCODE_OPTIONS=${VSCODE_OPTIONS:-""}

code $VSCODE_OPTIONS $ROOT_DIR
