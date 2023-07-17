import base64
import io
import json
import os

import cv2
from PIL import Image

from addons.storages import ImageStorage


def gen_frame(inf_img_strg: ImageStorage):
    ret, jpeg = cv2.imencode('.jpg', inf_img_strg.get_last_data())
    frame = jpeg.tobytes()
    return frame


def obj_imgs_to_str():
    counters_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "static", "counters", "counters.json"
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