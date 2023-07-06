import cv2
import numpy as np

from config import YOLOV5_CFG

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
        (YOLOV5_CFG["net_size"], YOLOV5_CFG["net_size"])
    )
    return frame