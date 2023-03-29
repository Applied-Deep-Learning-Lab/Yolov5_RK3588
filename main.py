import argparse
import time
from multiprocessing import Process
from threading import Thread

import addons.storages as strgs
from addons.byte_tracker import BTArgs, BYTETracker, draw_info, tracking
from addons.telegram_notifier import TelegramNotifier
from addons.webui import WebUI
from base import Rk3588, show_frames_localy


def fill_storages(
        rk3588: Rk3588,
        raw_img_strg: strgs.ImageStorage,
        inf_img_strg: strgs.ImageStorage,
        dets_strg: strgs.DetectionsStorage,
        start_time: float
):
    """Fill storages with raw frames, frames with bboxes, numpy arrays with
    detctions

    Args
    -----------------------------------
    rk3588 : Rk3588
        Object of Rk3588 class for getting data after inference
    raw_img_strg : storages.ImageStorage
        Object of ImageStorage for storage raw frames
    inf_img_strg : storages.ImageStorage
        Object of ImageStorage for storage inferenced frames
    dets_strg : storages.DetectionsStorage
        Object of DetectionsStorage for numpy arrays with detctions
    start_time : float
        Program start time
    -----------------------------------
    """
    while True:
            output = rk3588.get_data()
            if output is not None:
                raw_img_strg.set_data(
                    data=output[0],
                    id=output[3],
                    start_time=start_time
                )
                inf_img_strg.set_data(
                    data=output[1],
                    id=output[3],
                    start_time=start_time
                )
                dets_strg.set_data(
                    data=output[2],
                    id=output[3],
                    start_time=start_time
                )


def fill_storages_bytetracker(
        rk3588: Rk3588,
        raw_img_strg: strgs.ImageStorage,
        inf_img_strg: strgs.ImageStorage,
        dets_strg: strgs.DetectionsStorage,
        start_time: float
):
    """Fill storages with raw frames, frames with bboxes, numpy arrays with
    bytetrack detctions
    
    Args
    -----------------------------------
    rk3588 : Rk3588
        Object of Rk3588 class for getting data after inference
    raw_img_strg : storages.ImageStorage
        Object of ImageStorage for storage raw frames
    inf_img_strg : storages.ImageStorage
        Object of ImageStorage for storage inferenced frames
    dets_strg : storages.DetectionsStorage
        Object of DetectionsStorage for numpy arrays with bytetrack detctions
    start_time : float
        Program start time
    -----------------------------------
    """
    bytetrack_args = BTArgs()
    bytetracker = BYTETracker(
        args = bytetrack_args,
        frame_rate = 60
    )
    while True:
        output = rk3588.get_data()
        if output is not None:
            raw_frame, inferenced_frame, detections, frame_id = output
            if detections is not None:
                detections = tracking(
                    bytetracker=bytetracker,
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


def parse_opt():
    """Using for turn on/off addons"""
    parser = argparse.ArgumentParser()
    # add required arguments
    # required = parser.add_argument_group('required arguments')

    # some reqired args

    # add optional arguments
    parser.add_argument(
        "--storages",
        action = "store_true",
        help = "Turn on/off storages"
    )
    parser.add_argument(
        "--show",
        action = "store_true",
        help = "Show frames from storage or not"
    )
    parser.add_argument(
        "--webui",
        action = "store_true",
        help = "Turn on/off webui"
    )
    parser.add_argument(
        "--notifier", "-n",
        action = "store_true",
        help = "Turn on/off telegram bot notifier"
    )
    parser.add_argument(
        "--bytetracker", "-bt",
        action = "store_true",
        help = "Turn on/off BYTEtracker"
    )
    return parser.parse_args()


def main(
        storages: bool,
        show: bool,
        webui: bool,
        notifier: bool,
        bytetracker: bool
):
    """Runs inference and addons (if mentions)
    Creating storages and sending data to them

    Args
    -----------------------------------
    storages: bool
        Turn on/off storages
        Gets from parse_opt
    show: bool
        Show frames from storage or not
        Gets from parse_opt
    webui: bool
        Turn on/off web user interface
        Gets from parse_opt
    notifier: bool
        Turn on/off telegram bot notifier
        Gets from parse_opt
    bytetracker: bool
        Turn on/off BYTEtrack
        Gets from parse_opt
    -----------------------------------
    """
    rk3588 = Rk3588()
    start_time = time.time()
    if not storages:
        try:
            rk3588.start()
            while True:
                rk3588.show(start_time)
        except Exception as e:
            print("Main exception: {}".format(e))
            exit()
    raw_frames_storage = strgs.ImageStorage(
        strgs.StoragePurpose.RAW_FRAME
    )
    inferenced_frames_storage = strgs.ImageStorage(
        strgs.StoragePurpose.INFERENCED_FRAME
    )
    detections_storage = strgs.DetectionsStorage()
    if bytetracker:
        fill_thread = Thread(
            target = fill_storages_bytetracker,
            kwargs = {
                "rk3588" : rk3588,
                "raw_img_strg" : raw_frames_storage,
                "inf_img_strg" : inferenced_frames_storage,
                "dets_strg" : detections_storage,
                "start_time" : start_time
            },
            daemon = True
        )
    else:
        fill_thread = Thread(
            target = fill_storages,
            kwargs = {
                "rk3588" : rk3588,
                "raw_img_strg" : raw_frames_storage,
                "inf_img_strg" : inferenced_frames_storage,
                "dets_strg" : detections_storage,
                "start_time" : start_time
            },
            daemon = True
        )
    rk3588.start()
    fill_thread.start()
    if notifier:
        telegram_notifier = TelegramNotifier(
            inf_img_strg=inferenced_frames_storage
        )
        notifier_process = Process(
            target=telegram_notifier.start,
            daemon=True
        )
        try:
            notifier_process.start()
        except Exception as e:
            print("Bot exception: {}".format(e))
    if webui:
        ui = WebUI(
            raw_img_strg = raw_frames_storage,
            inf_img_strg = inferenced_frames_storage,
            dets_strg = detections_storage
        )
        try:
            ui.start()
        except Exception as e:
            print("WebUI exception: {}".format(e))
        finally:
            raw_frames_storage.clear_buffer()
            inferenced_frames_storage.clear_buffer()
            detections_storage.clear_buffer()
            exit()
    try:
        show_frames_localy(inferenced_frames_storage, start_time, show)
    except Exception as e:
        print("Main exception: {}".format(e))
    finally:
        raw_frames_storage.clear_buffer()
        inferenced_frames_storage.clear_buffer()
        detections_storage.clear_buffer()


if __name__ == "__main__":
    opt = parse_opt()
    main(**vars(opt))