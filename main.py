from base import Rk3588
from addons import storages as strgs
from addons import fill_storages, show_frames
from addons.webui import webUI
from threading import Thread


def main():
    raw_frames_storage = strgs.ImageStorage(
        strgs.StoragePurpose.RAW_FRAME
    )
    inferenced_frames_storage = strgs.ImageStorage(
        strgs.StoragePurpose.INFERENCED_FRAME
    )
    detections_storage = strgs.DetectionsStorage()
    rk3588 = Rk3588()
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
    ui = webUI(
        raw_img_strg = raw_frames_storage,
        inf_img_strg = inferenced_frames_storage,
        dets_strg = detections_storage
    )
    try:
        rk3588.start()
        fill_thread.start()
        ui.start()
    finally:
        raw_frames_storage.clear_buffer()
        inferenced_frames_storage.clear_buffer()
        detections_storage.clear_buffer()
        return
    # rk3588.start()
    # fill_thread.start()
    # while True:
    #     try:
    #         print(detections_storage.get_data_by_index(0))
    #         show_frames(inferenced_frames_storage.get_last_data())
    #     except:
    #         raw_frames_storage.clear_buffer()
    #         inferenced_frames_storage.clear_buffer()
    #         detections_storage.clear_buffer()
    #         break


if __name__ == "__main__":
    main()