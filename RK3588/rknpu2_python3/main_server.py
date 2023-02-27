from modules import config
from modules.camera.variable_camera import VariableCamera
from modules.inference.rknn_yolov5_variable import VariableYolov5
from modules.post_process.post_process_bytetracker import post_process
from modules.post_process.bytetracker_draw_storages import bytetracker_draw
import modules.storages as strg
from multiprocessing import Process, Queue
from rknnlite.api import RKNNLite


class OrangePi():
    def __init__(self):
        self._q_pre = Queue(maxsize=config.BUF_SIZE)
        self._q_outs = Queue(maxsize=config.BUF_SIZE)
        self._q_post = Queue(maxsize=config.BUF_SIZE)
        self._q_show = Queue(maxsize=config.BUF_SIZE)
        self._q_settings = Queue(maxsize=1)
        self._q_model = Queue(maxsize=1)

        self._raw_img_strg = strg.ImageStorage(
            storage_name = strg.StoragePurpose.RAW_FRAME
        )
        self._inf_img_strg = strg.ImageStorage(
            storage_name = strg.StoragePurpose.INFERENCED_FRAME
        )
        self._detections_strg = strg.DetectionsStorage()
        self._storages = [self._raw_img_strg, self._inf_img_strg, self._detections_strg]

        self._cores = [RKNNLite.NPU_CORE_0, RKNNLite.NPU_CORE_1, RKNNLite.NPU_CORE_2]

        self._cam = VariableCamera(
            source = config.SOURCE,
            q_in = self._q_show,
            q_out = self._q_pre,
            q_settings = self._q_settings
        )
        self._yolov5 = [
            VariableYolov5(
                proc = i,
                q_in = self._q_pre,
                q_out = self._q_outs,
                q_model = self._q_model,
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
                    'q_in': self._q_outs,
                    'q_out': self._q_post
                },
                daemon = True
            ) for i in range(config.POST_PROC)
        ]
        self._bytetracker = Process(
            target = bytetracker_draw,
            kwargs = {
                'q_in': self._q_post,
                'q_out': self._q_show,
                'storages': self._storages
            },
            daemon = True
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

    def get_data(self, index, storage_name):
        if storage_name == strg.StoragePurpose.RAW_FRAME:
            return self._raw_img_strg.get_data(index)
        if storage_name == strg.StoragePurpose.INFERENCED_FRAME:
            return self._inf_img_strg.get_data(index)
        if storage_name == strg.StoragePurpose.DETECTIONS:
            return self._detections_strg.get_data(index)

    def load_model(self, model: str):
        if isinstance(model, bytes):
            with open(config.NEW_MODEL, 'wb') as f:
                f.write(model)
            model = config.NEW_MODEL
        for proc in range(config.INF_PROC):
            self._q_model.put(model)

    def load_settings(self, settings: dict):
        self._q_settings.put(settings)


def main():
    orange = OrangePi()
    orange.start()
    while True:
        orange.show()


if __name__ == "__main__":
    main()