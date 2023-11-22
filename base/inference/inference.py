import os
from multiprocessing import Queue

from rknnlite.api import RKNNLite

from config import RK3588_CFG, Config
from log import DefaultLogger

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
MODELS = os.path.join(ROOT, "models")

# Create the inference's logger
logger = DefaultLogger("inference")


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
            net_cfg: Config,
            q_in: Queue,
            q_out: Queue,
            core: int = RKNNLite.NPU_CORE_AUTO
    ):
        self._q_in = q_in
        self._q_out = q_out
        self._core = core
        self._default_model = os.path.join(MODELS, net_cfg["default_model"])
        self._new_model = os.path.join(MODELS, net_cfg["new_model"])
        #Check new model loaded
        try:
            if os.path.isfile(self._new_model):
                logger.info("Load new model")
                self._ret = self._load_model(self._new_model)
            else:
                logger.info("Load default model")
                self._ret = self._load_model(self._default_model)
            if self._ret == -1:
                raise SystemExit
        except KeyboardInterrupt:
            logger.warning("Model loading stopped by keyboard interrupt")
        except Exception as e:
            logger.error(f"Cannot load model. Exception {e}")
            raise SystemExit

    def _load_model(self, path_to_model: str):
        model_name = path_to_model.split('/')[-1].split('.')[0]
        logger.info(f"{model_name}")
        self._rknnlite = RKNNLite(
            verbose=RK3588_CFG["verbose"],
            verbose_file=os.path.join(ROOT, RK3588_CFG["verbose_file"])
        )
        logger.info(f"{model_name}: Export rknn model")
        ret = self._rknnlite.load_rknn(path_to_model)
        if ret != 0:
            logger.error(f"{model_name}: Export rknn model failed!")
            return ret
        logger.info(f"{model_name}: Init runtime environment")
        ret = self._rknnlite.init_runtime(
            async_mode=RK3588_CFG["inference"]["async_mode"],
            core_mask = self._core
        )
        if ret != 0:
            logger.error(
                f"{model_name}: Init runtime environment failed!"
            )
            return ret
        logger.info(f"{model_name}: Model loaded")
        return ret

    def inference(self):
        try:
            while True:
                frame, raw_frame, frame_id = self._q_in.get()
                outputs = self._rknnlite.inference(inputs=[frame])
                if outputs is None:
                    raise KeyboardInterrupt
                self._q_out.put((outputs, raw_frame, frame_id))
        except KeyboardInterrupt:
            logger.warning("Inference stopped by keyboard interrupt")
