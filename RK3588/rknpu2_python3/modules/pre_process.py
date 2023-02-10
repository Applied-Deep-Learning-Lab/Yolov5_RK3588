from modules import config
import cv2

def pre_process(frame):
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    frame = cv2.resize(frame, (config.NET_SIZE, config.NET_SIZE))
    return frame