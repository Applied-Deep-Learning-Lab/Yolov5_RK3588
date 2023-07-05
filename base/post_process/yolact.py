from multiprocessing import Queue

import numpy as np

import cv2

from base.inference.utils import (after_nms_numpy, get_anchors, nms_numpy,
                                  permute, rknn_draw)


def yolact_post_process(q_in: Queue, q_out: Queue):
    while True:
        outputs, raw_frame, frame_id = q_in.get()
        # dets = None
        results = permute(outputs)
        anchors = get_anchors()
        results = nms_numpy(*results, anchors)
        results = after_nms_numpy(*results, 544, 544)
        frame = cv2.resize(raw_frame, (544, 544))
        frame = rknn_draw(frame, *results)
        q_out.put((frame, raw_frame, frame_id))