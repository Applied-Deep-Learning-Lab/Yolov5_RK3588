from multiprocessing import Queue

import numpy as np

import base.post_process as rknn_pp
from base.utils import format_dets


def post_process(q_in: Queue, q_out: Queue):
    """Overlays bboxes on frames

    Args
    -----------------------------------
    q_in : multiprocessing.Queue
        Queue that data reads from
    q_out : multiprocessing.Queue
        Queue that data sends to
    -----------------------------------
    """
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
                classes = classes, # type: ignore
                scores = scores # type: ignore
            )
        if q_out.full():
            continue
        q_out.put((raw_frame, frame, dets, frame_id))