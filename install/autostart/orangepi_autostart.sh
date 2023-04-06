#!/bin/bash

# Get absolute path to Conda environment
CONDA_ENV_PATH=$(conda info --envs | grep '^rknn' | awk '{print $2}')

# Get script parent folder
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Get absolute path to main.py
OBJ_DET_PROG=$(dirname $(dirname "$DIR"))/main.py

# Check if "exit 0" line exists in /etc/rc.local
if grep -q "^exit 0$" /etc/rc.local; then
    # Remove "exit 0" line from /etc/rc.local
    sudo sed -i '/^exit 0$/d' /etc/rc.local
    # Append LD_PRELOAD and python commands
    echo "Appending LD_PRELOAD and python commands"
    sudo tee -a /etc/rc.local > /dev/null <<EOF
export LD_PRELOAD=$LD_PRELOAD:/usr/lib/aarch64-linux-gnu/libffi.so.7
exec $CONDA_ENV_PATH/bin/python3 $OBJ_DET_PROG
EOF
fi

sudo /etc/rc.local start