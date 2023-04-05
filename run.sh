#!/bin/bash

# Get absolute path to Conda environment
CONDA_ENV_PATH=$(conda info --envs | grep '^rknn' | awk '{print $2}')

# Get script parent folder
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

$CONDA_ENV_PATH/bin/python3 $DIR/main.py