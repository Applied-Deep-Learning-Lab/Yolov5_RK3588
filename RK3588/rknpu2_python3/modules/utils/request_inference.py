from modules import config
from modules import storages as strg
from modules.utils.formatting import img_to_file, to_labelme
from zipfile import ZipFile
from datetime import datetime
import numpy as np


async def request_inference(detections_strg: strg.DetectionsStorage, raw_img_strg: strg.ImageStorage):
    zip_path = "inference.zip"
    last_index = detections_strg.get_last_index()
    with ZipFile(zip_path, 'w') as zip_file:
        for i in range(config.AMOUNT_OF_SEND_DATA):
            raw_image = raw_img_strg.get_data((last_index - i) % config.DATA_AMOUNT)
            dets = detections_strg.get_data((last_index - i) % config.DATA_AMOUNT)
            if not np.any(dets):
                if i == 0:
                    print("No frames")
                else:
                    print("Amount less then %d"%(config.AMOUNT_OF_SEND_DATA))
                break
            name = datetime.now().strftime('%Y-%m-%d.%H-%M-%S.%f')
            zip_file.writestr(
                f'{name}.png',
                img_to_file(raw_image)
            )
            zip_file.writestr(
                f'{name}.json',
                to_labelme(
                    content=(raw_image, dets),
                    classes=config.TRACKING_CLASSES,
                    frame_size=(config.CAM_WIDTH, config.CAM_HEIGHT),
                    image_path=name
                )
            )
    return zip_path