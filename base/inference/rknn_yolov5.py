from rknnlite.api import RKNNLite
import config
from multiprocessing import Queue

class Yolov5():
    def __init__(self, proc: int, q_in: Queue, q_out: Queue, core: int = RKNNLite.NPU_CORE_AUTO):
        self._q_in = q_in
        self._q_out = q_out
        self._core = core
        self._proc = proc
        self._total_inf_time = 0
        self._inf_time = 0
        self._frames = 0
        self._load_model(config.RKNN_MODEL)

    def _load_model(self, model: str):
        print("proc: ", self._proc)
        self._rknnlite = RKNNLite(verbose=config.VERBOSE, verbose_file=config.VERBOSE_FILE)

        print("%d. Export rknn model"%(self._proc))
        ret = self._rknnlite.load_rknn(model)
        if ret != 0:
            print('%d. Export rknn model failed!'%(self._proc))
            exit(ret)
        print('%d. done'%(self._proc))

        print('%d. Init runtime environment'%(self._proc))
        ret = self._rknnlite.init_runtime(async_mode=config.ASYNC_MODE, core_mask = self._core)
        if ret != 0:
            print('%d. Init runtime environment failed!'%(self._proc))
            exit(ret)
        print('%d. done'%(self._proc))

    def inference(self):
        while True:
            if self._q_in.empty():
                continue
            frame, raw_frame, frame_id = self._q_in.get()
            outputs = self._rknnlite.inference(inputs=[frame])
            if self._q_out.full():
                continue
            self._q_out.put((outputs, raw_frame, frame_id))