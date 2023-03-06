import utils.post_process as rknn_pp
from utils import format_dets
import numpy as np
from multiprocessing import Queue


def post_process(q_in: Queue, q_out: Queue):
    while True:
        if q_in.empty():
            continue
        outputs, raw_frame, frame_id = q_in.get()
        frame = raw_frame.copy()
        dets = None
        data = list()
        for out in outputs:
            out = out.reshape([3, -1]+list(out.shape[-2:]))
            data.append(np.transpose(out, (2, 3, 0, 1)))
        boxes, classes, scores = rknn_pp.yolov5_post_process(data)
        if boxes is not None:
            rknn_pp.draw(frame, boxes, scores, classes)
            dets = format_dets(
                boxes = boxes,
                classes = classes,
                scores = scores
            )
        if q_out.full():
            continue
        q_out.put((raw_frame, frame, dets, frame_id))