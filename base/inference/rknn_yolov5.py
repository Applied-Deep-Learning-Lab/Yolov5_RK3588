import json
import logging
import os
from multiprocessing import Queue
from pathlib import Path

from rknnlite.api import RKNNLite

ROOT = str(Path(__file__).parent.parent.parent.absolute())
MODELS = ROOT + "/models/"
CONFIG_FILE = ROOT + "/config.json"
with open(CONFIG_FILE, 'r') as config_file:
    cfg = json.load(config_file)

# Create the inference's logger
inference_logger = logging.getLogger("inference")
inference_logger.setLevel(logging.DEBUG)
inference_handler = logging.FileHandler(
    os.path.join(
        ROOT,
        "log/inference.log"
    )
)
inference_formatter = logging.Formatter(
    fmt="%(levelname)s - %(asctime)s: %(message)s.",
    datefmt="%d-%m-%Y %H:%M:%S"
)
inference_handler.setFormatter(inference_formatter)
inference_logger.addHandler(inference_handler)


class Yolov5():
    """Class for inference on RK3588/RK3588S

    Args
    ---------------------------------------------------------------------------
    proc : int
        Number of running process for inference
    q_in : multiprocessing.Queue
        Queue that data reads from
    q_out : multiprocessing.Queue
        Queue that data sends to
    core : int
        Index of NPU core(s) that will be used for inference
        default (RKNNLite.NPU_CORE_AUTO) : sets all cores for inference 
        one frame
    ---------------------------------------------------------------------------

    Attributes
    ---------------------------------------------------------------------------
    _q_out : multiprocessing.Queue
        Queue that data sends to
    _q_in : multiprocessing.Queue
        Queue that data reads from
    _core : int
        Index of NPU core that will be used for inference
    _proc : int
        Number of running process for inference
    ---------------------------------------------------------------------------

    Methods
    ---------------------------------------------------------------------------
    _load_model(model: str) : Literal[-1, 0]
        Load rknn model on RK3588/RK3588S device
    inference() : NoReturn
        inference resized raw frames
    ---------------------------------------------------------------------------
    """
    def __init__(
            self,
            proc: int,
            q_in: Queue,
            q_out: Queue,
            core: int = RKNNLite.NPU_CORE_AUTO
    ):
        self._q_in = q_in
        self._q_out = q_out
        self._core = core
        self._proc = proc
        #Check new model loaded
        try:
            if os.path.isfile(MODELS + cfg["inference"]["new_model"]):
                self._ret =self._load_model(
                    MODELS + cfg["inference"]["new_model"]
                )
            else:
                self._ret = self._load_model(
                    MODELS + cfg["inference"]["default_model"]
                )
        except Exception as e:
            inference_logger.error(f"Cannot load model. Exception {e}")
            raise SystemExit

    def _load_model(self, model: str):
        inference_logger.info(f"proc: {self._proc}")
        self._rknnlite = RKNNLite(
            verbose=cfg["debug"]["verbose"],
            verbose_file=ROOT + '/' + cfg["debug"]["verbose_file"]
        )
        inference_logger.info(f"{self._proc}. Export rknn model")
        ret = self._rknnlite.load_rknn(model)
        if ret != 0:
            inference_logger.error(f"{self._proc}. Export rknn model failed!")
            return ret
        inference_logger.info(f"{self._proc}. Init runtime environment")
        ret = self._rknnlite.init_runtime(
            async_mode=cfg["inference"]["async_mode"],
            core_mask = self._core
        )
        if ret != 0:
            inference_logger.error(
                f"{self._proc}. Init runtime environment failed!"
            )
            return ret
        inference_logger.info(f"{self._proc}. {model} model loaded")
        return ret

    def inference(self):
        while True:
            frame, raw_frame, frame_id = self._q_in.get()
            outputs = self._rknnlite.inference(inputs=[frame])
            self._q_out.put((outputs, raw_frame, frame_id))