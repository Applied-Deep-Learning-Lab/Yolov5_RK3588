import utils.post_process as rknn_pp
from utils import storages as strgs
from utils import format_dets
import numpy as np
from multiprocessing import Queue


def post_process(q_in: Queue, q_out: Queue, storages: list = None):
    while True:
        if q_in.empty():
            continue
        outputs, raw_frame, frame_id = q_in.get()
        frame = raw_frame.copy()
        data = list()
        for out in outputs:
            out = out.reshape([3, -1]+list(out.shape[-2:]))
            data.append(np.transpose(out, (2, 3, 0, 1)))
        boxes, classes, scores = rknn_pp.yolov5_post_process(data)
        if boxes is not None:
            rknn_pp.draw(frame, boxes, scores, classes)
            if storages is not None:
                dets = format_dets(
                    boxes = boxes,
                    classes = classes,
                    scores = scores
                )
                for storage in storages:
                    if storage.storage_name == strgs.StoragePurpose.RAW_FRAME:
                        storage.set_data(raw_frame)
                    elif storage.storage_name == strgs.StoragePurpose.INFERENCED_FRAME:
                        storage.set_data(frame)
                    elif storage.storage_name == strgs.StoragePurpose.DETECTIONS:
                        storage.set_data(dets)
        if q_out.full():
            continue
        q_out.put((frame, frame_id))