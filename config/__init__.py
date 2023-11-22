import json
import os
import sys
from multiprocessing import Queue
from typing import Callable, NoReturn, Union

from log import DefaultLogger

# Add the proj dir to the PYTHONPATH
proj_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, proj_dir)

# Create logger
logger = DefaultLogger("config")

RK3588_CFG_FILE = os.path.join(os.path.dirname(__file__), "rk3588_config.json")
YOLACT_CFG_FILE = os.path.join(os.path.dirname(__file__), "yolact_config.json")
PIDNET_CFG_FILE = os.path.join(os.path.dirname(__file__), "pidnet_config.json")
YOLOV5_CFG_FILE = os.path.join(os.path.dirname(__file__), "yolov5_config.json")


class Config(dict):
    def __init__(
            self,
            path_to_cfg: str
    ) -> None:
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

    def upload(self) -> bool:
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

    def add_post_proc_func(
            self,
            post_proc_func: Callable[[Queue, Queue], Union[NoReturn, None]]
    ):
        self.post_proc_func = post_proc_func


RK3588_CFG = Config(RK3588_CFG_FILE)
YOLACT_CFG = Config(YOLACT_CFG_FILE)
PIDNET_CFG = Config(PIDNET_CFG_FILE)
YOLOV5_CFG = Config(YOLOV5_CFG_FILE)

from base.post_process.yolact import yolact_post_process
from base.post_process.pidnet import pidnet_post_process
from base.post_process.yolov5 import yolov5_post_process

YOLACT_CFG.add_post_proc_func(yolact_post_process)
PIDNET_CFG.add_post_proc_func(pidnet_post_process)
YOLOV5_CFG.add_post_proc_func(yolov5_post_process)