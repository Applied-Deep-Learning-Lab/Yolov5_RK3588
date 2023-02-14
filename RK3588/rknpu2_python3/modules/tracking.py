from modules.byte_tracker import BYTETracker, BTArgs
from modules import config
from modules import rkkn_post_process as rknn_pp
import numpy as np
import cv2


def format_dets(boxes, classes, scores):
    # Creating np.array for detections
    dets=np.zeros([len(boxes), 6], dtype=np.float64)
    count=0
    # Formating boxes, classes, scores in dets (np.array) for input to bytetracker
    for box, score, cl in zip(boxes, scores, classes):
        top, left, right, bottom = box
        top = int(top*(config.CAM_WIDTH/config.NET_SIZE))
        left = int(left*(config.CAM_HEIGHT/config.NET_SIZE))
        right = int(right*(config.CAM_WIDTH/config.NET_SIZE))
        bottom = int(bottom*(config.CAM_HEIGHT/config.NET_SIZE))
        dets[count]=[top, left, right, bottom, cl, score]
        count+=1
    
    dets = dets[np.where(np.isin(dets[..., 4], [62]))]
    return dets


def tracking(bytetracker, dets, frame_shape):
    output = bytetracker.update(dets, frame_shape, frame_shape)
    output = [np.append(out.tlbr, [out.track_id, out.sclass]) for out in output]
    if len(output):
        return np.asarray(output)


def draw_bytetracker(frame, dets):
    for det in dets:
        cv2.rectangle(img=frame,
            pt1=(int(det[0]), int(det[1])),
            pt2=(int(det[2]), int(det[3])),
            color=(123, 0, 123),
            thickness=1)
        cv2.putText(
            img=frame,
            text="%d - %d"%(det[5], det[4]),
            org=(int(det[0]) + 3, int(det[1]) + 3),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=0.6,
            color=(0,123,0),
            thickness=2,
            lineType=cv2.LINE_AA
        )


def post_process(lock, q_outs, q_post):
    bytetrack_args = BTArgs()
    bytetracker = BYTETracker(bytetrack_args, frame_rate=60)
    while True:
        outputs, frame, frame_id = q_outs.get()
        data = list()
        for out in outputs:
            out = out.reshape([3, -1]+list(out.shape[-2:]))
            data.append(np.transpose(out, (2, 3, 0, 1)))
        boxes, classes, scores = rknn_pp.yolov5_post_process(data)
        if boxes is not None:
            dets=format_dets(boxes, classes, scores)
            dets=tracking(bytetracker, dets, frame.shape[:2])
            if dets is not None:
                draw_bytetracker(frame,dets)
            rknn_pp.draw(frame, boxes, scores, classes)
        if q_post.full():
            continue
        with lock:
            q_post.put((frame, frame_id))