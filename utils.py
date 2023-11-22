import base64
import io
import json
import os
import time
from threading import Event
from typing import Union

import cv2
from PIL import Image

import addons.storages as strgs
from addons.byte_tracker import BYTETracker, draw_info, tracking
from addons.pulse_counter import Monitor
from base import Rk3588
from config import RK3588_CFG
from log import DefaultLogger

# Create logger
logger = DefaultLogger("utils")


def obj_imgs_to_str():
    """Convert detection's images for show them at the WebUI"""
    counters_file = os.path.join(
        os.path.dirname(__file__),
        "resources", "counters", "counters.json"
    )
    with open(counters_file, 'r') as json_file:
        counters = json.load(json_file)
    for counter in counters:
        img_path = os.path.join(
            os.path.dirname(counters_file),
            counters[counter]["img_path"]
        )
        if os.path.isdir(img_path):
            continue
        img = Image.open(img_path)
        img = img.resize((80, 80))
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue())
        img_str = str(img_str)[2:-1]
        counters[counter]["img_src"] = "data:image/png;base64," + img_str
    with open(counters_file, 'w') as json_file:
        json.dump(
            obj=counters,
            fp=json_file,
            indent=4
        )


def fill_storages(
        stop_event: Event,
        rk3588: Rk3588,
        tracker: Union[BYTETracker, Monitor, None],
        raw_img_strg: strgs.ImageStorage,
        inf_img_strg: strgs.ImageStorage,
        dets_strg: Union[strgs.Storage, strgs.DetectionsStorage]
):
    """Fill storages with raw frames, frames with bboxes, numpy arrays with detctions

    Args
    -----------------------------------
    stop_event: Event
        Event stopping filling of storages by exception from another part of the program
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
    try:
        while not stop_event.is_set():
            output = rk3588.get_data()[0]
            if output is not None:
                inferenced_frame, raw_frame, detections, frame_id = output
                detections_id = frame_id
                # Tracking detections
                if detections is not None:
                    # ByteTracker
                    if type(tracker) is BYTETracker:
                        # Track objects and write it's ids and another data to the storage
                        detections = tracking(
                            bytetracker=tracker,
                            dets=detections,
                            frame_shape=inferenced_frame.shape[:2]
                        )
                        # Draw ids at inferenced frame
                        if detections is not None:
                            draw_info(
                                frame=inferenced_frame,
                                dets=detections
                            )
                    # Pulse Monitor
                    elif type(tracker) is Monitor:
                        detections_id = 0
                        # Track and count detections
                        tracker.update(detections)
                        detections = tracker.up_counter
                        # Draw dot on inferenced frame for pulse counting
                        if tracker.signal:
                            cv2.rectangle(
                                img=inferenced_frame,
                                pt1=(inferenced_frame.shape[1] // 2 - 4, 50),
                                pt2=(inferenced_frame.shape[1] // 2 + 4, 58),
                                color=(0, 0, 128),
                                thickness=8
                            )

                raw_img_strg.set_data(
                    data=raw_frame,
                    id=frame_id
                )
                cv2.rectangle(
                    img=inferenced_frame,
                    pt1=(inferenced_frame.shape[1] // 2 - 4, 50),
                    pt2=(inferenced_frame.shape[1] // 2 + 4, 58),
                    color=(128, 0, 0),
                    thickness=4
                )
                inf_img_strg.set_data(
                    data=inferenced_frame,
                    id=frame_id
                )
                dets_strg.set_data(
                    data=detections,
                    id=detections_id
                )
        logger.warning(
            "Filling storages stopped by keyboard interrupt or system exit"
        )
    except ValueError as e:
        logger.error(
            f"Probably cannot write data storage. Try set size for it. {e}"
        )
    except Exception as e:
        logger.error(f"Got exception - {e}")


def do_counting(
        inf_img_strg: strgs.ImageStorage,
        dets_strg: strgs.DetectionsStorage,
        counters_strg: strgs.Storage,
        pulse_monitor: Monitor,
        start_time: float = time.time()
):
    """Counts yolov5's detctions"""
    stored_data_amount = RK3588_CFG["storages"]["stored_data_amount"]
    # for fps
    begin_time = time.time()
    counter = 0
    calculated = False
    cur_index = -1
    try:
        while True:
            last_index = dets_strg.get_last_index()
            if last_index > cur_index:
                cur_index = last_index
            else:
                continue
            dets = dets_strg.get_data_by_index(last_index % stored_data_amount)
            if dets is not None:
                pulse_monitor.update(dets)
            img = inf_img_strg.get_data_by_index(last_index % stored_data_amount)
            if pulse_monitor.signal:
                cv2.rectangle(
                    img=img,
                    pt1=(img.shape[1] // 2 - 4, 50), # type: ignore
                    pt2=(img.shape[1] // 2 + 4, 58), # type: ignore
                    color=(0, 0, 128),
                    thickness=8
                )
                counters_strg.set_data(
                    data=pulse_monitor.up_counter,
                    id=0
                )
            if RK3588_CFG["pulse_counter"]["plot"]:
                pulse_monitor.plot_graph(time.time() - start_time)
            if RK3588_CFG["count_fps"]:
                counter += 1
                if counter % RK3588_CFG["camera"]["fps"] == 0 and not calculated:
                    calculated = True
                    fps = RK3588_CFG["camera"]["fps"]/(time.time() - begin_time)
                    begin_time = time.time()
                    logger.debug(f"{fps:.2f}")
                if counter % RK3588_CFG["camera"]["fps"] != 0:
                    calculated = False
    except KeyboardInterrupt:
        logger.warning("Program stoped while do counting")
    except Exception as e:
        logger.error(f"Got exception - {e}")
        raise SystemExit


def show_frames_localy(
        inf_img_strg: strgs.ImageStorage,
        start_time: float,
        stop_event: Event
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
    stored_data_amount = RK3588_CFG["storages"]["stored_data_amount"]
    try:
        while True:
            if stop_event.is_set():
                raise KeyboardInterrupt
            last_index = inf_img_strg.get_last_index()
            if RK3588_CFG["debug"] and cur_index != last_index:
                logger.debug(
                    "show_local_{}\t{:.3f}".format(
                        cur_index,
                        time.time() - start_time
                    )
                )
            frame = inf_img_strg.get_data_by_index(
                last_index % stored_data_amount
            )
            if RK3588_CFG["camera"]["show"]:
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
            if counter % RK3588_CFG["camera"]["fps"] == 0 and not calculated:
                calculated = True
                fps = RK3588_CFG["camera"]["fps"]/(time.time() - begin_time)
                begin_time = time.time()
            if counter % RK3588_CFG["camera"]["fps"] != 0:
                calculated = False
    except KeyboardInterrupt:
        cv2.destroyAllWindows()
        logger.warning("Local showing stopped by keyboard interrupt")
    except SystemExit:
        cv2.destroyAllWindows()
        logger.error("Local showing stopped by system exit")
    except Exception as e:
        logger.error(f"Local showing stopped by {e}")
        raise SystemExit
