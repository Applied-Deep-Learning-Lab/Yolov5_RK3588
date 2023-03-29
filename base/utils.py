import json
import time
from pathlib import Path

import cv2
import numpy as np

import addons.storages as strgs


CONFIG_FILE = str(Path(__file__).parent.parent.absolute()) + "/config.json"
with open(CONFIG_FILE, 'r') as config_file:
    cfg = json.load(config_file)


def format_dets(boxes: np.ndarray, classes: np.ndarray, scores: np.ndarray):
    """Formating detections to numpy array
    ([top, left, right, bottom, class, score])

    Args
    -----------------------------------
    boxes : np.ndarray
        boxes of objects
    classes : np.ndarray
        classes of objects
    scores : np.ndarray
        scores of objects
    -----------------------------------
    """
    dets=np.zeros([len(boxes), 6], dtype=np.float32)
    count=0
    width = cfg["camera"]["width"]
    height = cfg["camera"]["height"]
    net_size = cfg["inference"]["net_size"]
    for box, score, cl in zip(boxes, scores, classes):
        top, left, right, bottom = box
        top = int(top*(width / net_size))
        left = int(left*(height / net_size))
        right = int(right*(width / net_size))
        bottom = int(bottom*(height / net_size))
        dets[count]=[top, left, right, bottom, cl, score]
        count+=1
    return dets


def show_frames_localy(
        inf_img_strg: strgs.ImageStorage,
        start_time: float,
        show: bool
):
    """Show inferenced frames with fps on device
    
    Args
    -----------------------------------
    inf_img_strg : storages.ImageStorage
        Object of ImageStorage for storage inferenced frames
    start_time : float
        Program start time
    show: bool
        Show frames from storage or not
        Gets from parse_opt
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
        frame =\
            inf_img_strg.get_data_by_index(last_index % stored_data_amount)
        if show:
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