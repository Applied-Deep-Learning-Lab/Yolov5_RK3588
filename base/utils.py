import json
from pathlib import Path

import cv2
import numpy as np


CONFIG_FILE = str(Path(__file__).parent.parent.absolute()) + "/config.json"
with open(CONFIG_FILE, 'r') as config_file:
    cfg = json.load(config_file)


def format_dets(boxes: np.ndarray, classes: np.ndarray, scores: np.ndarray):
    """Formating detections to numpy array
    ([top, left, right, bottom, class, score])

    Args
    -----------------------------------
    boxes : np.ndarray
        boxes of objects
    classes : np.ndarray
        classes of objects
    scores : np.ndarray
        scores of objects
    -----------------------------------
    """
    dets=np.zeros([len(boxes), 6], dtype=np.float32)
    count=0
    width = cfg["camera"]["width"]
    height = cfg["camera"]["height"]
    net_size = cfg["inference"]["net_size"]
    for box, score, cl in zip(boxes, scores, classes):
        top, left, right, bottom = box
        top = int(top*(width / net_size))
        left = int(left*(height / net_size))
        right = int(right*(width / net_size))
        bottom = int(bottom*(height / net_size))
        dets[count]=[top, left, right, bottom, cl, score]
        count+=1
    return dets


def show_frames(frame):
    """Showes frames"""
    cv2.imshow("frame", frame)
    cv2.waitKey(1)