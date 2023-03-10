from config import config_from_json
from pathlib import Path
import cv2
import numpy as np

CONFIG_FILE = str(Path(__file__).parent.parent.parent.absolute()) + "/config.json"
cfg = config_from_json(CONFIG_FILE, read_from_file = True)
Mat = np.ndarray[int, np.dtype[np.generic]]


def pre_process(frame: Mat):
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    frame = cv2.resize(frame, (cfg["inference"]["net_size"], cfg["inference"]["net_size"]))
    return frame