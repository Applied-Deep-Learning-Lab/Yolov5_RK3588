import numpy as np

from config import RK3588_CFG, YOLOV5_CFG


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
    width = RK3588_CFG["camera"]["width"]
    height = RK3588_CFG["camera"]["height"]
    net_size = YOLOV5_CFG["net_size"]
    for box, score, cl in zip(boxes, scores, classes):
        top, left, right, bottom = box
        top = int(top*(width / net_size))
        left = int(left*(height / net_size))
        right = int(right*(width / net_size))
        bottom = int(bottom*(height / net_size))
        dets[count]=[top, left, right, bottom, cl, score]
        count+=1
    return dets