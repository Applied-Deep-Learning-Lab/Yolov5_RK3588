import base64
import io
import json
import logging
import os
from datetime import datetime
from zipfile import ZipFile

import cv2
import numpy as np
from PIL import Image

from addons.storages import DetectionsStorage, ImageStorage
from config import RK3588_CFG

# Create the server's logger
ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
)
server_logger = logging.getLogger("server")
server_logger.setLevel(logging.DEBUG)
server_handler = logging.FileHandler(
    os.path.join(
        ROOT,
        "log/server.log"
    )
)
server_formatter = logging.Formatter(
    fmt="%(levelname)s - %(asctime)s: %(message)s.",
    datefmt="%d-%m-%Y %H:%M:%S"
)
server_handler.setFormatter(server_formatter)
server_logger.addHandler(server_handler)


def gen_frame(inf_img_strg: ImageStorage):
    ret, jpeg = cv2.imencode('.jpg', inf_img_strg.get_last_data())
    frame = jpeg.tobytes()
    return frame


def obj_imgs_to_str():
    counters_file = os.path.join(
        ROOT,
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


def boxes_to_shapes(bboxes, classes):
    """Convert bounding boxes to labelme shapes
        Parameters:
            bboxes(numpy.ndarray[[x1, y1, x2, y2, class, score]...]) - Array
                of bounding boxes
            classes(list(str)) - List of neural network class names
        Returns:
            res(list(dict)) - List of dictionaries contains labelme shapes
    """
    res = []
    if bboxes is not None:
        for bb in bboxes:
            try:
                class_name = classes[int(bb[4])]
            except:
                class_name = int(bb[4])
            res.append({
                "label": f"{class_name}",
                "points": [
                    [int(bb[0]), int(bb[1])],
                    [int(bb[2]), int(bb[3])]
                ],
                "group_id": None,
                "shape_type": "rectangle",
                "flags": {}
            })
    return res


def img_to_file(img_arr):
    """Convert OpenCV2 image to binary form
        Parameters:
            img_arr(numpy.ndarray) - OpenCV2 image
        Returns:
            img_bin(bytes) - Binary representation of image in PNG format
    """
    img_arr = img_arr[:, :, ::-1]  # Convert BGR to RGB
    img_pil = Image.fromarray(img_arr)
    f = io.BytesIO()
    img_pil.save(f, format="PNG")
    img_bin = f.getvalue()
    return img_bin


def img_arr_to_b64(img_arr):
    """Convert image to base64 string format
        Parameters:
            img_arr(numpy.ndarray) - OpenCV2 image
        Returns:
            img_b64(bytes) - Base64 representation of image
    """
    img_bin = img_to_file(img_arr)
    if hasattr(base64, "encodebytes"):
        img_b64 = base64.encodebytes(img_bin)
    else:
        img_b64 = base64.encodestring(img_bin)  # type: ignore
    return img_b64


def to_labelme(content, classes, frame_size, image_path=None):
    """Convert inference data to labelme format
        Parameters:
            content(tuple(numpy.ndarray, numpy.ndarray)) - Frameswith
                corresponding bounding boxes
            classes(list(str)) - List of neural network class names
            frame_size(tuple(int)) - Frame width and height
            image_path(str) - Relative image path
    """
    labelme_dict = {
        'version': '4.5.6',
        'flags': {},
        'imageHeight': frame_size[1],
        'imageWidth': frame_size[0],
        'shapes': boxes_to_shapes(content[1], classes),
        'imageData': img_arr_to_b64(content[0]).decode('utf-8')
    }
    if image_path is not None:
        labelme_dict['imagePath'] = image_path
    else:
        labelme_dict['imagePath'] = ''
    labelme_json = json.dumps(labelme_dict, indent=4)
    return labelme_json


def request_inference(
    dets_strg: DetectionsStorage,
    raw_img_strg: ImageStorage
):
    """Send last frames with bboxes to client in labelme format

    Args
    -----------------------------------
    dets_strg : storages.DetectionsStorage
        Object of DetectionsStorage that stored numpy array with detections
    raw_img_strg : storages.ImageStorage
        Object of ImageStorage that stored raw frames
    -----------------------------------
    """
    file_path = os.path.dirname(__file__)
    zip_path = file_path + "/inference.zip"
    last_index = dets_strg.get_last_index()
    with ZipFile(zip_path, 'w') as zip_file:
        for i in range(RK3588_CFG["webui"]["send_data_amount"]):
            raw_img = raw_img_strg.get_data_by_index(
                (last_index - i) % RK3588_CFG["storages"]["stored_data_amount"]
            )
            dets = dets_strg.get_data_by_index(
                (last_index - i) % RK3588_CFG["storages"]["stored_data_amount"]
            )
            dets = dets[np.where(dets[..., 5] > 0)]  # type: ignore
            if not np.any(dets):
                if i == 0:
                    server_logger.warning("No frames")
                else:
                    server_logger.warning(
                        'Amount less then {}'.format(
                            RK3588_CFG["webui"]["send_data_amount"]
                        )
                    )
                break
            name = datetime.now().strftime('%Y-%m-%d.%H-%M-%S.%f')
            zip_file.writestr(
                f'{name}.png',
                img_to_file(raw_img)
            )
            zip_file.writestr(
                f'{name}.json',
                to_labelme(
                    content=(raw_img, dets),
                    classes=RK3588_CFG["bytetrack"]["tracking_classes"],
                    frame_size=(
                        RK3588_CFG["camera"]["width"],
                        RK3588_CFG["camera"]["height"]
                    ),
                    image_path=name
                )
            )
    return zip_path
