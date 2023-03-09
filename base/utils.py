import config
import numpy as np
import cv2


def format_dets(boxes: np.ndarray, classes: np.ndarray, scores: np.ndarray):
    dets=np.zeros([len(boxes), 6], dtype=np.float32)
    count=0
    for box, score, cl in zip(boxes, scores, classes):
        top, left, right, bottom = box
        top = int(top*(config.CAM_WIDTH/config.NET_SIZE))
        left = int(left*(config.CAM_HEIGHT/config.NET_SIZE))
        right = int(right*(config.CAM_WIDTH/config.NET_SIZE))
        bottom = int(bottom*(config.CAM_HEIGHT/config.NET_SIZE))
        dets[count]=[top, left, right, bottom, cl, score]
        count+=1
    # dets = dets[np.where(np.isin(dets[..., 4], config.TRACKING_CLASSES))]
    return dets


def show_frames(frame):
    cv2.imshow("frame", frame)
    cv2.waitKey(1)