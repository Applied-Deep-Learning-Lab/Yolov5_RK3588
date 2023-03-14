from config import config_from_json
from pathlib import Path
from base.camera import Cam
from base.inference import Yolov5
from base.post_process import post_process
from multiprocessing import Process, Queue
from rknnlite.api import RKNNLite

# Getting config
CONFIG_FILE = str(Path(__file__).parent.parent.absolute()) + "/config.json"
cfg = config_from_json(CONFIG_FILE, read_from_file = True)


class Rk3588():
    def __init__(self):
        # Creating queues for sending data between processes
        self._q_pre = Queue(maxsize=cfg["inference"]["buf_size"])
        self._q_outs = Queue(maxsize=cfg["inference"]["buf_size"])
        self._q_post = Queue(maxsize=cfg["inference"]["buf_size"])
        # Creating camera object for recording frames process
        self._cam = Cam(
            source = cfg["camera"]["source"],
            q_in = self._q_post,
            q_out = self._q_pre
        )
        # Creating list with names of npu cores
        self._cores = [RKNNLite.NPU_CORE_0, RKNNLite.NPU_CORE_1, RKNNLite.NPU_CORE_2]
        # Creating yolov5 objects for inferencing frames processes
        self._yolov5 = [
            Yolov5(
                proc = i,
                q_in = self._q_pre,
                q_out = self._q_outs,
                core = self._cores[i%3]
            ) for i in range(cfg["inference"]["inf_proc"])
        ]
        # Creating process for recording frames
        self._rec = Process(
            target = self._cam.record,
            daemon=True
        )
        # Creating processes for inferencing frames
        self._inf = [
            Process(
                target = self._yolov5[i].inference,
                daemon = True
            ) for i in range(len(self._yolov5))
        ]
        # Creating processes for post processing frames
        self._post = [
            Process(
                target = post_process,
                kwargs = {
                    "q_in" : self._q_outs,
                    "q_out" : self._q_post
                },
                daemon=True
            ) for i in range(cfg["inference"]["post_proc"])
        ]
        
    def start(self):
        #Starting all processes
        self._rec.start()
        for inference in self._inf: inference.start()
        for post_process in self._post: post_process.start()

    def show(self):
        self._cam.show()

    def get_data(self):
        if self._q_post.empty():
            return None
        raw_frame, inferenced_frame, detections, frame_id = self._q_post.get()
        return(raw_frame, inferenced_frame, detections, frame_id)