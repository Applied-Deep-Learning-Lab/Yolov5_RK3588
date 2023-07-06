import logging
import os
from multiprocessing import Queue

from rknnlite.api import RKNNLite

from config import RK3588_CFG

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
MODELS = os.path.join(ROOT, "models")

# Create the inference's logger
inference_logger = logging.getLogger("inference")
inference_logger.setLevel(logging.DEBUG)
# Create handler that output all info to the console
inference_console_handler = logging.StreamHandler()
inference_console_handler.setLevel(logging.DEBUG)
# Create handler that output errors, warnings to the file
inference_file_handler = logging.FileHandler(
    os.path.join(
        ROOT,
        "log/inference.log"
    )
)
inference_file_handler.setLevel(logging.ERROR)
# Create formatter for handlers
inference_formatter = logging.Formatter(
    fmt="%(levelname)s - %(asctime)s: %(message)s.",
    datefmt="%d-%m-%Y %H:%M:%S"
)
inference_console_handler.setFormatter(inference_formatter)
inference_file_handler.setFormatter(inference_formatter)
# Add handlers to the logger
inference_logger.addHandler(inference_console_handler)
inference_logger.addHandler(inference_file_handler)


class NeuralNetwork():
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
    _name : int
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
            model: str,
            q_in: Queue,
            q_out: Queue,
            core: int = RKNNLite.NPU_CORE_AUTO
    ):
        self._q_in = q_in
        self._q_out = q_out
        self._core = core
        self._name = model.split('.')[0]
        #Check new model loaded
        try:
            self._ret =self._load_model(
                os.path.join(MODELS, model)
            )
        except Exception as e:
            inference_logger.error(f"Cannot load model. Exception {e}")
            raise SystemExit

    def _load_model(self, path_to_model: str):
        inference_logger.info(f"{self._name}")
        self._rknnlite = RKNNLite(
            verbose=RK3588_CFG["verbose"],
            verbose_file=os.path.join(ROOT, RK3588_CFG["verbose_file"])
        )
        inference_logger.info(f"{self._name}: Export rknn model")
        ret = self._rknnlite.load_rknn(path_to_model)
        if ret != 0:
            inference_logger.error(f"{self._name}: Export rknn model failed!")
            return ret
        inference_logger.info(f"{self._name}: Init runtime environment")
        ret = self._rknnlite.init_runtime(
            async_mode=RK3588_CFG["inference"]["async_mode"],
            core_mask = self._core
        )
        if ret != 0:
            inference_logger.error(
                f"{self._name}: Init runtime environment failed!"
            )
            return ret
        inference_logger.info(f"{self._name}: Model loaded")
        return ret

    def inference(self):
        while True:
            frame, raw_frame, frame_id = self._q_in.get()
            outputs = self._rknnlite.inference(inputs=[frame])
            self._q_out.put((outputs, raw_frame, frame_id))