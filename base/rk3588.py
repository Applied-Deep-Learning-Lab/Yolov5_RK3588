from multiprocessing import Process, Queue

from rknnlite.api import RKNNLite

from base.camera import Cam
from base.inference import NeuralNetwork
from base.post_process import pidnet_post_process, yolact_post_process
from config import RK3588_CFG


class Rk3588():
    """Class for object detection on RK3588/RK3588S
    
    Attributes
    ---------------------------------------------------------------------------

    Queues
    -----------------------------------
    _q_pre : multiprocessing.Queue
        Queue for sending raw frames, resized frames and frames ids from
        camera reading process to inference process
    _q_outs : multiprocessing.Queue
        Queue for sending inference results, raw frames and frames ids from
        inference process to post_process process
    _q_post : multiprocessing.Queue
        Queue for sending raw frames, frames with bboxes, numpy array with
        detections and frames ids from post_process process to ouput
    -----------------------------------

    Camera
    -----------------------------------
    cam : camera.Cam
        Camera object for creating recording, showing process
    -----------------------------------

    Inference
    -----------------------------------
    _yolov5 : inference.Yolov5 or inference.VariableYolov5
        Yolov5 object for creating inference processes
    -----------------------------------

    Processes
    -----------------------------------
    _rec : multiprocessing.Process
        Process for recording frames
    _inf : multiprocessing.Process
        Process for inferencing frames (recomended amount is 3 and should equal
        post_process processes)
    _post : multiprocessing.Process
        Process for post processing frames (recomended amount is 3 and should
        equal inference processes)
    -----------------------------------
    ---------------------------------------------------------------------------
    
    Methods
    ---------------------------------------------------------------------------
    start() : None
        Starts all processes (recording process, inference process(es),
        post_process process(es))
    show() : None
        Create cv2 window with inferenced frames (frames with bboxes on them)
    get_data() : tuple(np.ndarray, np.ndarray, np.ndarray, int) | None
        Returns raw frames, frames with bboxes, numpy array with detections
        and frames ids
    ---------------------------------------------------------------------------
    """
    def __init__(self):
        # Create queues for pre process
        self._yolact_q_pre = Queue(maxsize=RK3588_CFG["inference"]["buf_size"])
        self._pidnet_q_pre = Queue(maxsize=RK3588_CFG["inference"]["buf_size"])
        # Create queues for inference
        self._yolact_q_outs = Queue(maxsize=RK3588_CFG["inference"]["buf_size"])
        self._pidnet_q_outs = Queue(maxsize=RK3588_CFG["inference"]["buf_size"])
        # Create queues for post process
        self._yolact_q_post = Queue(maxsize=RK3588_CFG["inference"]["buf_size"])
        self._pidnet_q_post = Queue(maxsize=RK3588_CFG["inference"]["buf_size"])
        self._cam = Cam(
            source=RK3588_CFG["camera"]["source"],
            nn_sizes=(544, 768),
            q_in=(self._yolact_q_post, self._pidnet_q_post),
            q_out=(self._yolact_q_pre, self._pidnet_q_pre)
        )
        self._yolact = NeuralNetwork(
            name="yolact",
            model="yolact_544.rknn",
            q_in=self._yolact_q_pre,
            q_out=self._yolact_q_outs,
            core=RKNNLite.NPU_CORE_0_1
        )
        self._pidnet = NeuralNetwork(
            name="pidnet",
            model="pidnet_drone_int8-s.rknn",
            q_in=self._pidnet_q_pre,
            q_out=self._pidnet_q_outs,
            core=RKNNLite.NPU_CORE_2
        )
        self._rec = Process(
            target = self._cam.record,
            daemon=True
        )
        self._yolact_inf = Process(
            target = self._yolact.inference,
            daemon = True
        )
        self._pidnet_inf = Process(
            target = self._pidnet.inference,
            daemon = True
        )
        self._yolact_post = Process(
            target = yolact_post_process,
            kwargs = {
                "q_in" : self._yolact_q_outs,
                "q_out" : self._yolact_q_post
            },
            daemon=True
        )
        self._pidnet_post = Process(
            target = pidnet_post_process,
            kwargs = {
                "q_in" : self._pidnet_q_outs,
                "q_out" : self._pidnet_q_post
            },
            daemon=True
        )

    def start(self):
        self._rec.start()
        self._yolact_inf.start()
        self._pidnet_inf.start()
        self._yolact_post.start()
        self._pidnet_post.start()

    def show(self, start_time):
        self._cam.show(start_time)

    def get_data(self):
        # WIP
        return None
        # if self._q_post.empty():
        #     return None
        # raw_frame, inferenced_frame, detections, frame_id = self._q_post.get()
        # return(raw_frame, inferenced_frame, detections, frame_id)