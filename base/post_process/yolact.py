from multiprocessing import Queue
from typing import NoReturn

import cv2

from base.post_process.utils import (after_nms_numpy, get_anchors, nms_numpy,
                                     permute, rknn_draw)
from config import YOLACT_CFG


def yolact_post_process(q_in: Queue, q_out: Queue) -> NoReturn:
    while True:
        outputs, raw_frame, frame_id = q_in.get()
        dets = None
        results = permute(outputs)
        anchors = get_anchors()
        results = nms_numpy(*results, anchors)
        results = after_nms_numpy(
            *results,
            YOLACT_CFG["net_size"],
            YOLACT_CFG["net_size"]
        )
        frame = cv2.resize(
            raw_frame,
            (YOLACT_CFG["net_size"], YOLACT_CFG["net_size"])
        )
        frame = rknn_draw(frame, *results)
        q_out.put((frame, raw_frame, dets, frame_id))