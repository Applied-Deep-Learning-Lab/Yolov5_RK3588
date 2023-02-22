from modules.byte_tracker import BYTETracker, BTArgs
from modules import config
import numpy as np
import cv2


def format_dets(boxes, classes, scores):
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
    dets = dets[np.where(np.isin(dets[..., 4], config.TRACKING_CLASSES))]
    return dets


def tracking(bytetracker, dets, frame_shape):
    output = bytetracker.update(dets, frame_shape, frame_shape)
    output = [np.append(out.tlbr, [out.track_id, out.sclass]) for out in output]
    if len(output):
        return np.asarray(output)


def draw_info(frame, dets):
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


def bytetracker_draw(q_in, q_out):
    bytetrack_args = BTArgs()
    bytetracker = BYTETracker(bytetrack_args, frame_rate=config.BYTETRACKER_FPS)
    while True:
        if q_in.empty():
            continue
        frame, frame_id, raw_frame, dets = q_in.get()
        boxes, classes, scores = dets
        if boxes is not None:
            dets=format_dets(boxes, classes, scores)
            dets=tracking(bytetracker, dets, frame.shape[:2])
            if dets is not None:
                draw_info(frame,dets)
        if q_out.full():
            continue
        q_out.put((frame, frame_id))