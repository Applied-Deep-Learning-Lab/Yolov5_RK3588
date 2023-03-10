from config import config_from_json
from pathlib import Path
import numpy as np
import cv2


CONFIG_FILE = str(Path(__file__).parent.parent.absolute()) + "/config.json"
cfg = config_from_json(CONFIG_FILE, read_from_file = True)


def format_dets(boxes: np.ndarray, classes: np.ndarray, scores: np.ndarray):
    dets=np.zeros([len(boxes), 6], dtype=np.float32)
    count=0
    for box, score, cl in zip(boxes, scores, classes):
        top, left, right, bottom = box
        top = int(top*(cfg["camera"]["width"]/cfg["inference"]["net_size"]))
        left = int(left*(cfg["camera"]["height"]/cfg["inference"]["net_size"]))
        right = int(right*(cfg["camera"]["width"]/cfg["inference"]["net_size"]))
        bottom = int(bottom*(cfg["camera"]["height"]/cfg["inference"]["net_size"]))
        dets[count]=[top, left, right, bottom, cl, score]
        count+=1
    # dets = dets[np.where(np.isin(dets[..., 4], cfg["bytetrack"]["tracking_classes"]))]
    return dets


def show_frames(frame):
    cv2.imshow("frame", frame)
    cv2.waitKey(1)