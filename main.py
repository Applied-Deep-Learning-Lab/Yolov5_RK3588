from base import Rk3588
from base import show_frames
import addons.storages as strgs
from addons.byte_tracker import BYTETracker, BTArgs
from addons.byte_tracker import tracking, draw_info
from threading import Thread
import argparse
from addons.webui import webUI


def fill_storages(rk3588: Rk3588, raw_img_strg: strgs.ImageStorage, inf_img_strg: strgs.ImageStorage, dets_strg: strgs.DetectionsStorage):
    while True:
            output = rk3588.get_data()
            if output is not None:
                raw_img_strg.set_data(output[0])
                inf_img_strg.set_data(output[1])
                dets_strg.set_data(output[2])


def fill_storages_bytetracker(rk3588: Rk3588, raw_img_strg: strgs.ImageStorage, inf_img_strg: strgs.ImageStorage, dets_strg: strgs.DetectionsStorage):
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
            dets_strg.set_data(detections)


def parse_opt():
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
    raw_frames_storage = strgs.ImageStorage(
        strgs.StoragePurpose.RAW_FRAME
    )
    inferenced_frames_storage = strgs.ImageStorage(
        strgs.StoragePurpose.INFERENCED_FRAME
    )
    detections_storage = strgs.DetectionsStorage()
    rk3588 = Rk3588()
    if bytetracker:
        fill_thread = Thread(
            target = fill_storages_bytetracker,
            kwargs = {
                "rk3588" : rk3588,
                "raw_img_strg" : raw_frames_storage,
                "inf_img_strg" : inferenced_frames_storage,
                "dets_strg" : detections_storage
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
                "dets_strg" : detections_storage
            },
            daemon = True
        )
    rk3588.start()
    fill_thread.start()
    if webui:
        ui = webUI(
            raw_img_strg = raw_frames_storage,
            inf_img_strg = inferenced_frames_storage,
            dets_strg = detections_storage
        )
        try:
            ui.start()
        finally:
            raw_frames_storage.clear_buffer()
            inferenced_frames_storage.clear_buffer()
            detections_storage.clear_buffer()
            return
    else:
        while True:
            try:
                show_frames(inferenced_frames_storage.get_last_data())
            except:
                raw_frames_storage.clear_buffer()
                inferenced_frames_storage.clear_buffer()
                detections_storage.clear_buffer()
                break


if __name__ == "__main__":
    opt = parse_opt()
    main(**vars(opt))