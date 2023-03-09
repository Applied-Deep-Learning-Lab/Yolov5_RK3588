import numpy as np
import cv2
from addons.byte_tracker import BYTETracker


def draw_info(frame: np.ndarray, dets: np.ndarray):
    for det in dets:
        cv2.rectangle(img=frame,
            pt1=(int(det[0]) + 10, int(det[1]) + 10),
            pt2=(int(det[2] - 10), int(det[3]) - 10),
            color=(123, 0, 123),
            thickness=1)
        cv2.putText(
            img=frame,
            text="%d - %d"%(det[5], det[4]),
            org=(int(det[0]) + 13, int(det[3]) - 13),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=0.6,
            color=(0,123,0),
            thickness=2,
            lineType=cv2.LINE_AA
        )


def tracking(bytetracker: BYTETracker, dets: np.ndarray, frame_shape: tuple):
    output = bytetracker.update(dets, frame_shape, frame_shape)
    output = [np.append(out.tlbr, [out.track_id, out.sclass]) for out in output]
    if len(output):
        return np.asarray(output)
    else:
        return None