#!/bin/bash

# Get absolute path to Conda environment
CONDA_ENV_PATH=$(conda info --envs | grep '^rknn' | awk '{print $2}')

# Get script parent folder
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Get absolute path to autostart service
AUTOSTART_SERVICE=$DIR/obj_det_autostart.service

# Get absolute path to main.py
OBJ_DET_PROG=$(dirname $(dirname "$DIR"))/main.py

# Set permissions for cp/rm service file
if [ $(whoami) <> 'root' ]; then
    sudo chmod 777 /etc/systemd/system
    sudo chmod 777 $AUTOSTART_SERVICE
    rm ./root
    rm $DIR/root
fi

# Remove prev autostart service
service obj_det_autostart stop
rm -rf /etc/systemd/system/obj_det_autostart.service

# Set "Exec" line in .desktop file
sed -i "s|ExecStart=.*|ExecStart=$CONDA_ENV_PATH/bin/python3 $OBJ_DET_PROG|" $AUTOSTART_SERVICE

# Send autostart service to system folder
cp $AUTOSTART_SERVICE /etc/systemd/system/

# Reload the systemd daemon to read the new service file
systemctl daemon-reload

# Start autostart service
service obj_det_autostart start