from rknnlite.api import RKNNLite
from config import config_from_json
from pathlib import Path
from multiprocessing import Queue


CONFIG_FILE = str(Path(__file__).parent.parent.parent.absolute()) + "/config.json"
cfg = config_from_json(CONFIG_FILE, read_from_file = True)


class Yolov5():
    def __init__(self, proc: int, q_in: Queue, q_out: Queue, core: int = RKNNLite.NPU_CORE_AUTO):
        self._q_in = q_in
        self._q_out = q_out
        self._core = core
        self._proc = proc
        self._total_inf_time = 0
        self._inf_time = 0
        self._frames = 0
        if self._load_model(cfg["inference"]["path_to_new_model"]) != 0:
            self._ret = self._load_model(cfg["inference"]["path_to_default_model"])

    def _load_model(self, model: str):
        print("proc: ", self._proc)
        self._rknnlite = RKNNLite(verbose=cfg["debug"]["verbose"], verbose_file=cfg["debug"]["verbose_file"])

        print("%d. Export rknn model"%(self._proc))
        ret = self._rknnlite.load_rknn(model)
        if ret != 0:
            print('%d. Export rknn model failed!'%(self._proc))
            return ret
        print('%d. done'%(self._proc))

        print('%d. Init runtime environment'%(self._proc))
        ret = self._rknnlite.init_runtime(async_mode=cfg["inference"]["async_mode"], core_mask = self._core)
        if ret != 0:
            print('%d. Init runtime environment failed!'%(self._proc))
            return ret
        print('%d. done with %s model'%(self._proc, model))
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