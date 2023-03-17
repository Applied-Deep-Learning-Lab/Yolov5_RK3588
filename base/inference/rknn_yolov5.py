import json
import os
from multiprocessing import Queue
from pathlib import Path

from rknnlite.api import RKNNLite


CONFIG_FILE = str(Path(__file__).parent.parent.parent.absolute()) + "/config.json"
with open(CONFIG_FILE, 'r') as config_file:
    cfg = json.load(config_file)


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
        if os.path.isfile(cfg["inference"]["path_to_new_model"]):
            self._load_model(
                cfg["inference"]["path_to_new_model"]
            )
        else:
            self._ret = self._load_model(
                cfg["inference"]["path_to_default_model"]
            )

    def _load_model(self, model: str):
        print("proc: ", self._proc)
        self._rknnlite = RKNNLite(
            verbose=cfg["debug"]["verbose"],
            verbose_file=cfg["debug"]["verbose_file"]
        )
        print("%d. Export rknn model"%(self._proc))
        ret = self._rknnlite.load_rknn(model)
        if ret != 0:
            print('%d. Export rknn model failed!'%(self._proc))
            return ret
        print('%d. Init runtime environment'%(self._proc))
        ret = self._rknnlite.init_runtime(
            async_mode=cfg["inference"]["async_mode"],
            core_mask = self._core
        )
        if ret != 0:
            print('%d. Init runtime environment failed!'%(self._proc))
            return ret
        print('%d. %s model loaded'%(self._proc, model))
        return ret

    def inference(self):
        while True:
            if self._q_in.empty():
                continue
            frame, raw_frame, frame_id = self._q_in.get()
            outputs = self._rknnlite.inference(inputs=[frame])
            if self._q_out.full():
                continue
            self._q_out.put((outputs, raw_frame, frame_id))