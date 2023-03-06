from base import Rk3588
from addons import storages as strgs
import cv2


def fill_storages(rk3588: Rk3588, raw_img_strg: strgs.ImageStorage, inf_img_strg: strgs.ImageStorage, dets_strg: strgs.DetectionsStorage):
    while True:
            output = rk3588.get_data()
            if output is not None:
                raw_img_strg.set_data(output[0])
                inf_img_strg.set_data(output[1])
                dets_strg.set_data(output[2])


def show_frames(frame):
    cv2.imshow("frame", frame)
    cv2.waitKey(1)