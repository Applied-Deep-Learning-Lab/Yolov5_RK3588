from modules.byte_tracker import BYTETracker, BTArgs
import multiprocessing as mp
import modules.storage_for_db as strg
from modules import config
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


def bytetracker_draw(lock: mp.Lock, q_in: mp.Queue, q_out: mp.Queue, img_storages: list[strg.ImageStorage] = None, data_storages: list[strg.DetectionsStorage] = None):
    bytetrack_args = BTArgs()
    bytetracker = BYTETracker(bytetrack_args, frame_rate=config.BYTETRACKER_FPS)
    while True:
        frame, frame_id, raw_frame, dets = q_in.get()
        boxes, classes, scores = dets
        if boxes is not None:
            dets=format_dets(boxes, classes, scores)
            dets=tracking(bytetracker, dets, frame.shape[:2])
            if dets is not None:
                draw_info(frame,dets)
        if q_out.full():
            continue
        if img_storages is not None:
            for storage in img_storages:
                # Check is the 'storage._index_counter' incrementing
                if storage._name is strg.StoragePurpose.RAW_FRAME:
                    if storage._index_counter == config.DATA_AMOUNT: storage._index_counter = 0
                    storage.set_data(raw_frame, storage._index_counter)
                elif storage._name is strg.StoragePurpose.INFERENCED_FRAME:
                    if storage._index_counter == config.DATA_AMOUNT: storage._index_counter = 0
                    storage.set_data(frame, storage._index_counter)
        if data_storages is not None:
            for storage in data_storages:
                if storage._name is strg.StoragePurpose.DETECTIONS:
                    if storage._index_counter == config.DATA_AMOUNT: storage._index_counter = 0
                    storage.set_data(dets, storage._index_counter)
        with lock:
            q_out.put((frame, frame_id))