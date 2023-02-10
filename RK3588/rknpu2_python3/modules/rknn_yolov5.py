from rknnlite.api import RKNNLite
import time
from modules import config

class Yolov5():
    def __init__(self, proc, lock, q_pre, q_outs, core=RKNNLite.NPU_CORE_AUTO):
        self._lock = lock
        self._q_pre = q_pre
        self._q_outs = q_outs
        self._core = core
        self._proc = proc
        self._total_inf_time = 0
        self._inf_time = 0
        self._frames = 0
        print("proc: ", self._proc)
        self._rknnlite = RKNNLite(verbose=config.VERBOSE, verbose_file=config.VERBOSE_FILE)

        print("%d. Export rknn model"%(self._proc))
        ret = self._rknnlite.load_rknn(config.RKNN_MODEL)
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
            if config.PRINT_DIF:
                frame, raw_frame, frame_id, start = self._q_pre.get()
            else:
                frame, raw_frame, frame_id = self._q_pre.get()
            outputs = self._rknnlite.inference(inputs=[frame])
            if config.PRINT_DIF:
                print('i%d id(%d) - %f'%(self._proc, frame_id, time.time() - start))
            if config.PRINT_TIME:
                print('i%d id(%d) - %f'%(self._proc, frame_id, time.time()))
            if self._q_outs.full():
                continue
            with self._lock:
                if config.PRINT_DIF:
                    self._q_outs.put((outputs, raw_frame, frame_id, start))
                else:
                    self._q_outs.put((outputs, raw_frame, frame_id))