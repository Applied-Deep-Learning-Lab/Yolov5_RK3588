import json
import logging
import os
from typing import Union

# Create logger
logger = logging.getLogger("config")
logger.setLevel(logging.DEBUG)
# Create handler that output all info to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
# Create handler that output errors, warnings to the file
file_handler = logging.FileHandler(
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "log/config.log"
    )
)
file_handler.setLevel(logging.ERROR)
# Create formatter
formatter = logging.Formatter(
    fmt="%(levelname)s - %(asctime)s: %(message)s.",
    datefmt="%d-%m-%Y %H:%M:%S"
)
# Add formtter to the handlers
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

RK3588_CFG_FILE = os.path.join(os.path.dirname(__file__), "rk3588_config.json")
YOLACT_CFG_FILE = os.path.join(os.path.dirname(__file__), "yolact_config.json")
PIDNET_CFG_FILE = os.path.join(os.path.dirname(__file__), "pidnet_config.json")
YOLOV5_CFG_FILE = os.path.join(os.path.dirname(__file__), "yolov5_config.json")


class Config(dict):
    def __init__(self, path_to_cfg: str) -> None:
        self._path = path_to_cfg
        data = []
        try:
            with open(self._path, 'r') as cfg_file:
                data = json.load(cfg_file)
        except Exception as e:
            logger.error(
                "{} get exception while init: {}".format(
                    self._path.split('/')[-1].split('.')[0], e
                )
            )
        finally:
            super().__init__(data)

    def update(self) -> bool:
        try:
            with open(self._path, 'w') as cfg_file:
                json.dump(
                    obj=self,
                    fp=cfg_file,
                    indent=4
                )
            return True
        except Exception as e:
            logger.error(
                "{} get exception while saving config: {}".format(
                    self._path.split('/')[-1].split('.')[0], e
                )
            )
            return False


RK3588_CFG = Config(RK3588_CFG_FILE)
YOLACT_CFG = Config(YOLACT_CFG_FILE)
PIDNET_CFG = Config(PIDNET_CFG_FILE)
YOLOV5_CFG = Config(YOLOV5_CFG_FILE)
