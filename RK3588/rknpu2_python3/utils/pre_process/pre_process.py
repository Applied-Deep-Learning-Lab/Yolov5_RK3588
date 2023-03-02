from modules import config
import cv2
import numpy as np

Mat = np.ndarray[int, np.dtype[np.generic]]

def pre_process(frame: Mat):
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    frame = cv2.resize(frame, (config.NET_SIZE, config.NET_SIZE))
    return frame