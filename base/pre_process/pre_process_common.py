import json
from pathlib import Path

import cv2
import numpy as np


CONFIG_FILE = str(Path(__file__).parent.parent.parent.absolute()) + "/config.json"
with open(CONFIG_FILE, 'r') as config_file:
    cfg = json.load(config_file)
Mat = np.ndarray[int, np.dtype[np.generic]]


def pre_process(frame: Mat):
    """Resizing raw frames from original size to net size

    Args
    -----------------------------------
    frame : np.ndarray
        Raw frame
    -----------------------------------
    """
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    frame = cv2.resize(
        frame,
        (cfg["inference"]["net_size"], cfg["inference"]["net_size"])
    )
    return frame