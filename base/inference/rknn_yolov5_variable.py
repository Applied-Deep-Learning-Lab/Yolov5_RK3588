from base.inference import Yolov5
from rknnlite.api import RKNNLite
from multiprocessing import Queue

class VariableYolov5(Yolov5):
    def __init__(self, proc: int, q_in: Queue, q_out: Queue, q_model: Queue, core: int = RKNNLite.NPU_CORE_AUTO):
        super().__init__(
            proc = proc,
            q_in = q_in,
            q_out = q_out,
            core = core
        )
        self._q_model = q_model

    def inference(self):
        while True:
            if not self._q_model.empty():
                model = self._q_model.get()
                self._load_model(model)
            if self._q_in.empty():
                continue
            frame, raw_frame, frame_id = self._q_in.get()
            outputs = self._rknnlite.inference(inputs=[frame])
            if self._q_out.full():
                continue
            self._q_out.put((outputs, raw_frame, frame_id))