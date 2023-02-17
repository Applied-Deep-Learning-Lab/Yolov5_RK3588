from modules import config
from modules.camera import Cam
from modules.rknn_yolov5 import Yolov5
from modules.post_process.post_process_bytetracker import post_process
from modules.post_process.bytetracker_draw import bytetracker_draw
import modules.storage_for_db as storage
import numpy as np
from multiprocessing import Process, Queue, Lock
from rknnlite.api import RKNNLite


class OrangePi():
    def __init__(self):
        self._q_pre = Queue(maxsize=config.BUF_SIZE)
        self._q_outs = Queue(maxsize=config.BUF_SIZE)
        self._q_post = Queue(maxsize=config.BUF_SIZE)
        self._q_show = Queue(maxsize=config.BUF_SIZE)

        self._raw_img_strg = storage.ImageStorage(
            storage_name = storage.StoragePurpose.RAW_FRAME
        )
        self._inf_img_strg = storage.ImageStorage(
            storage_name = storage.StoragePurpose.INFERENCED_FRAME
        )
        self._detections_strg = storage.DetectionsStorage()
        self._images_storages = [self._raw_img_strg, self._inf_img_strg]
        self._data_storages = [self._detections_strg]

        self._lock = Lock()
        self._cores = [RKNNLite.NPU_CORE_0, RKNNLite.NPU_CORE_1, RKNNLite.NPU_CORE_2]

        self._cam = Cam(
            source = config.SOURCE,
            lock = self._lock,
            q_in = self._q_show,
            q_out = self._q_pre
        )
        self._yolov5 = [
            Yolov5(
                proc = i,
                lock = self._lock,
                q_in = self._q_pre,
                q_out = self._q_outs,
                core = self._cores[i%3]
            ) for i in range(config.INF_PROC)
        ]
        self._rec = Process(
            target = self._cam.record,
            daemon = True
        )
        self._inf = [
            Process(
                target = self._yolov5[i].inference,
                daemon = True
            ) for i in range(config.INF_PROC)
        ]
        self._post = [
            Process(
                target = post_process,
                kwargs = {
                    'lock':self._lock,
                    'q_in': self._q_outs,
                    'q_out': self._q_post
                },
                daemon = True
            ) for i in range(config.POST_PROC)
        ]
        self._bytetracker = Process(
            target = bytetracker_draw,
            kwargs = {
                'lock' : self._lock,
                'q_in' : self._q_post,
                'q_out' : self._q_show,
                'img_storages' : self._images_storages,
                'data_storages':self._data_storages
            },
            daemon=True
        )

    def start(self):
        self._rec.start()
        for i in range(config.INF_PROC): self._inf[i].start()
        for i in range(config.POST_PROC): self._post[i].start()
        self._bytetracker.start()

    def show(self):
        self._cam.show()

    def get_frame(self):
        return self._cam.get_frame()


def main():
    pass


if __name__ == "__main__":
    main()