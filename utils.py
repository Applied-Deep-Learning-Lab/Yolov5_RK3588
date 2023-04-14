import json
import time
from pathlib import Path
from typing import Union

import cv2

import addons.storages as strgs
from addons.byte_tracker import BYTETracker, draw_info, tracking
from addons.pulse_counter import Monitor
from base import Rk3588

CONFIG_FILE = str(Path(__file__).parent.absolute()) + "/config.json"
with open(CONFIG_FILE, 'r') as config_file:
    cfg = json.load(config_file)


def fill_storages(
        rk3588: Rk3588,
        tracker: Union[BYTETracker, None],
        raw_img_strg: strgs.ImageStorage,
        inf_img_strg: strgs.ImageStorage,
        dets_strg: strgs.DetectionsStorage,
        start_time: float,
):
    """Fill storages with raw frames, frames with bboxes, numpy arrays with
    detctions

    Args
    -----------------------------------
    rk3588: Rk3588
        Object of Rk3588 class for getting data after inference
    raw_img_strg: storages.ImageStorage
        Object of ImageStorage for storage raw frames
    inf_img_strg: storages.ImageStorage
        Object of ImageStorage for storage inferenced frames
    dets_strg: storages.DetectionsStorage
        Object of DetectionsStorage for numpy arrays with detctions
    start_time: float
        Program start time
    tracker: BYTETracker | None
        detections tracker
    -----------------------------------
    """
    while True:
        output = rk3588.get_data()
        if output is not None:
            raw_frame, inferenced_frame, detections, frame_id = output
            # Bytetracker
            if tracker is not None and detections is not None:
                detections = tracking(
                    bytetracker=tracker,
                    dets=detections,
                    frame_shape=inferenced_frame.shape[:2]
                )
                if detections is not None:
                    draw_info(
                        frame=inferenced_frame,
                        dets=detections
                    )
            raw_img_strg.set_data(
                data=raw_frame,
                id=frame_id,
                start_time=start_time
            )
            cv2.rectangle(
                img=inferenced_frame,
                pt1=(316, 50),
                pt2=(324, 58),
                color=(128, 0, 0),
                thickness=4
            )
            inf_img_strg.set_data(
                data=inferenced_frame,
                id=frame_id,
                start_time=start_time
            )
            dets_strg.set_data(
                data=detections, # type: ignore
                id=frame_id,
                start_time=start_time
            )


def do_counting(
        inf_img_strg: strgs.ImageStorage,
        dets_strg: strgs.DetectionsStorage,
        counters_strg: strgs.Storage,
        pulse_monitor: Monitor
):
    stored_data_amount = cfg["storages"]["stored_data_amount"]
    while True:
        last_index = dets_strg.get_last_index()
        dets = dets_strg.get_data_by_index(last_index % stored_data_amount)
        if dets is not None:
            pulse_monitor.update(dets)
        img = inf_img_strg.get_data_by_index(last_index % stored_data_amount)
        if pulse_monitor.signal:
            cv2.rectangle(
                img=img,
                pt1=(316, 50),
                pt2=(324, 58),
                color=(0, 0, 128),
                thickness=8
            )
            counters_strg.set_data(
                data=pulse_monitor.up_counter,
                id=0
            )


def show_frames_localy(
        inf_img_strg: strgs.ImageStorage,
        start_time: float
):
    """Show inferenced frames with fps on device
    
    Args
    -----------------------------------
    inf_img_strg: storages.ImageStorage
        Object of ImageStorage for storage inferenced frames
    start_time: float
        Program start time
    -----------------------------------
    """
    cur_index = -1
    counter = 0
    calculated = False
    begin_time = time.time()
    fps = 0
    stored_data_amount = cfg["storages"]["stored_data_amount"]
    while True:
        last_index = inf_img_strg.get_last_index()
        if cfg["debug"]["showed_frame_id"] and cur_index != last_index:
            with open(cfg["debug"]["showed_id_file"], 'a') as f:
                f.write(
                    "{}\t{:.3f}\n".format(
                        cur_index,
                        time.time() - start_time
                    )
                )
        print(
            "cur - {} last - {}".format(
                cur_index,
                last_index
            ),
            end='\r'
        )
        frame = inf_img_strg.get_data_by_index(last_index % stored_data_amount)
        if cfg["camera"]["show"]:
            cv2.putText(
                img=frame,
                text="{:.2f}".format(fps),
                org=(5, 25),
                fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                fontScale=0.8,
                color=(255, 255, 255),
                thickness=2,
                lineType=cv2.LINE_AA
            )
            cv2.imshow("frame", frame)
            cv2.waitKey(1)
        if last_index > cur_index:
            counter += 1
            cur_index = last_index
        if counter % 60 == 0 and not calculated:
            calculated = True
            fps = 60/(time.time() - begin_time)
            begin_time = time.time()
        if counter % 60 != 0:
            calculated = False