from threading import Thread
from modules import storages as strgs
from modules.rk3588 import Rk3588
from modules.utils import fill_storages, show_frames


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
    rk3588.start()
    fill_thread.start()
    while True:
        try:
            show_frames(inferenced_frames_storage.get_last_data())
        except:
            raw_frames_storage.clear_buffer()
            inferenced_frames_storage.clear_buffer()
            detections_storage.clear_buffer()


if __name__ == "__main__":
    main()