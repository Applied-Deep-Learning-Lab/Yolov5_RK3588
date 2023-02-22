from modules.inference.rknn_yolov5 import Yolov5
from rknnlite.api import RKNNLite
import time
from modules import config

class VariableYolov5(Yolov5):
    def __init__(self, proc, lock, q_in, q_out, q_settings, core=RKNNLite.NPU_CORE_AUTO):
        super().__init__(
            proc = proc,
            lock = lock,
            q_in = q_in,
            q_out = q_out,
            core = core
        )
        self._q_settings = q_settings

    def inference(self):
        while True:
            if not self._q_settings.empty():
                model = self._q_settings.get()
                self._load_model(model)
            if self._q_in.empty():
                continue
            if config.PRINT_DIF:
                frame, raw_frame, frame_id, start = self._q_in.get()
            else:
                frame, raw_frame, frame_id = self._q_in.get()
            outputs = self._rknnlite.inference(inputs=[frame])
            if config.PRINT_DIF:
                print('i%d id(%d) - %f'%(self._proc, frame_id, time.time() - start))
            if config.PRINT_TIME:
                print('i%d id(%d) - %f'%(self._proc, frame_id, time.time()))
            if self._q_out.full():
                continue
            with self._lock:
                if config.PRINT_DIF:
                    self._q_out.put((outputs, raw_frame, frame_id, start))
                else:
                    self._q_out.put((outputs, raw_frame, frame_id))