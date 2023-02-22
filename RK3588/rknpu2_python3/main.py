from modules import config
from modules.camera.camera import Cam
from modules.inference.rknn_yolov5 import Yolov5
from modules.post_process.post_process_common import post_process
from multiprocessing import Process, Queue, Lock
from rknnlite.api import RKNNLite


class OrangePi():
    def __init__(self):
        self._q_pre = Queue(maxsize=config.BUF_SIZE)
        self._q_outs = Queue(maxsize=config.BUF_SIZE)
        self._q_post = Queue(maxsize=config.BUF_SIZE)
        self._lock = Lock()

        self._cam = Cam(config.SOURCE, self._lock, self._q_post, self._q_pre)
        self._cores = [RKNNLite.NPU_CORE_0, RKNNLite.NPU_CORE_1, RKNNLite.NPU_CORE_2]
        self._yolov5 = [Yolov5(i, self._lock, self._q_pre, self._q_outs, self._cores[i%3]) for i in range(config.INF_PROC)]

        self._rec = Process(target=self._cam.record, daemon=True)
        self._inf = [Process(target=self._yolov5[i].inference, daemon=True) for i in range(config.INF_PROC)]
        self._post = [Process(target=post_process, args=(i, self._lock, self._q_outs, self._q_post), daemon=True) for i in range(config.POST_PROC)]
        
    def start(self):
        self._rec.start()
        for i in range(config.INF_PROC): self._inf[i].start()
        for i in range(config.POST_PROC): self._post[i].start()

    def show(self):
        self._cam.show()

    def get_frame(self):
        return self._cam.get_frame()


def main():
    orange = OrangePi()
    orange.start()
    while True:
        orange.show()


if __name__ == '__main__':
    main()