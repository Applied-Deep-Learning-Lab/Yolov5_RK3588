from multiprocessing import Process
from threading import Thread
from modules import storages as strgs
from modules.rk3588 import Rk3588
import cv2


def fill(rk3588: Rk3588, raw_img_strg: strgs.ImageStorage, inf_img_strg: strgs.ImageStorage, dets_strg: strgs.DetectionsStorage):
    while True:
        output = rk3588.get_data()
        if output is not None:
            raw_img_strg.set_data(output[0])
            inf_img_strg.set_data(output[1])
            dets_strg.set_data(output[2])


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
        target = fill,
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
        print(detections_storage.get_last_data()[0])
        cv2.imshow("frame", inferenced_frames_storage.get_last_data())
        cv2.waitKey(1)


if __name__ == "__main__":
    main()