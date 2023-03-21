import argparse
from threading import Thread

import addons.storages as strgs
from addons.byte_tracker import BTArgs, BYTETracker, draw_info, tracking
from addons.webui import WebUI
from base import Rk3588, show_frames


def fill_storages(
    rk3588: Rk3588,
    raw_img_strg: strgs.ImageStorage,
    inf_img_strg: strgs.ImageStorage,
    dets_strg: strgs.DetectionsStorage
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
    -----------------------------------
    """
    last_id = 0
    while True:
            output = rk3588.get_data()
            if output is not None:
                if output[3] > last_id:
                    raw_img_strg.set_data(output[0])
                    inf_img_strg.set_data(output[1])
                    dets_strg.set_data(output[2])
                    last_id = output[3]


def fill_storages_bytetracker(
    rk3588: Rk3588,
    raw_img_strg: strgs.ImageStorage,
    inf_img_strg: strgs.ImageStorage,
    dets_strg: strgs.DetectionsStorage
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
                    bytetracker = bytetracker,
                    dets = detections,
                    frame_shape = inferenced_frame.shape[:2]
                )
                if detections is not None:
                    draw_info(
                        frame = inferenced_frame,
                        dets = detections
                    )
            raw_img_strg.set_data(raw_frame)
            inf_img_strg.set_data(inferenced_frame)
            dets_strg.set_data(detections) # type: ignore


def parse_opt():
    """Using for turn on/off addons"""
    parser = argparse.ArgumentParser()
    # add required arguments
    # required = parser.add_argument_group('required arguments')

    # some reqired args

    # add optional arguments
    parser.add_argument(
        "--webui",
        action = "store_true",
        help = "Turn on/off webui"
    )
    parser.add_argument(
        "--bytetracker", "-bt",
        action = "store_true",
        help = "Turn on/off BYTEtracker"
    )
    return parser.parse_args()


def main(webui: bool, bytetracker: bool):
    """Runs inference and addons (if mentions)
    Creating storages and sending data to them,

    Args
    -----------------------------------
    webui: bool
        Turn on/off web user interface
        Gets from parse_opt
    bytetracker: bool
        Turn on/off BYTEtrack
        Gets from parse_opt
    -----------------------------------
    """
    # raw_frames_storage = strgs.ImageStorage(
    #     strgs.StoragePurpose.RAW_FRAME
    # )
    # inferenced_frames_storage = strgs.ImageStorage(
    #     strgs.StoragePurpose.INFERENCED_FRAME
    # )
    # detections_storage = strgs.DetectionsStorage()
    rk3588 = Rk3588()
    # if bytetracker:
    #     fill_thread = Thread(
    #         target = fill_storages_bytetracker,
    #         kwargs = {
    #             "rk3588" : rk3588,
    #             "raw_img_strg" : raw_frames_storage,
    #             "inf_img_strg" : inferenced_frames_storage,
    #             "dets_strg" : detections_storage
    #         },
    #         daemon = True
    #     )
    # else:
    #     fill_thread = Thread(
    #         target = fill_storages,
    #         kwargs = {
    #             "rk3588" : rk3588,
    #             "raw_img_strg" : raw_frames_storage,
    #             "inf_img_strg" : inferenced_frames_storage,
    #             "dets_strg" : detections_storage
    #         },
    #         daemon = True
    #     )
    rk3588.start()
    while True:
        rk3588.show()
    # fill_thread.start()
    # if webui:
    #     ui = WebUI(
    #         raw_img_strg = raw_frames_storage,
    #         inf_img_strg = inferenced_frames_storage,
    #         dets_strg = detections_storage
    #     )
    #     try:
    #         ui.start()
    #     finally:
    #         raw_frames_storage.clear_buffer()
    #         inferenced_frames_storage.clear_buffer()
    #         detections_storage.clear_buffer()
    #         return
    # else:
    #     while True:
    #         try:
    #             show_frames(inferenced_frames_storage.get_last_data())
    #         except:
    #             raw_frames_storage.clear_buffer()
    #             inferenced_frames_storage.clear_buffer()
    #             detections_storage.clear_buffer()
    #             break


if __name__ == "__main__":
    opt = parse_opt()
    main(**vars(opt))