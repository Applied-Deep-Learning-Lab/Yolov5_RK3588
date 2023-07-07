from multiprocessing import Process, Queue
from typing import Union

from rknnlite.api import RKNNLite

from base.camera import Cam
from base.inference import NeuralNetwork
from config import RK3588_CFG, Config


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
    def __init__(
            self,
            first_net_cfg: Config,
            second_net_cfg: Union[Config, None] = None
    ):
        self._first_net_cfg = first_net_cfg
        self._second_net_cfg = second_net_cfg
        # Create queues
        self._first_net_q_pre = Queue(
            maxsize=RK3588_CFG["inference"]["buf_size"]
        )
        self._first_net_q_outs = Queue(
            maxsize=RK3588_CFG["inference"]["buf_size"]
        )
        self._first_net_q_post = Queue(
            maxsize=RK3588_CFG["inference"]["buf_size"]
        )
        # Create obj for a neural network
        self._first_net = NeuralNetwork(
            model=self._first_net_cfg["default_model"],
            q_in=self._first_net_q_pre,
            q_out=self._first_net_q_outs,
            core=RKNNLite.NPU_CORE_0_1
        )
        # Create inference process for a neural network
        self._first_net_inf = Process(
            target = self._first_net.inference,
            daemon = True
        )
        # Create post process process for a neural network
        self._first_net_post = Process(
            target = self._first_net_cfg.post_proc_func,
            kwargs = {
                "q_in" : self._first_net_q_outs,
                "q_out" : self._first_net_q_post
            },
            daemon=True
        )
        # Create the same things for a second neural network if it exists
        if self._second_net_cfg is not None:
            # Create queues for a second neural network
            self._second_net_q_pre = Queue(
                maxsize=RK3588_CFG["inference"]["buf_size"]
            )
            self._second_net_q_outs = Queue(
                maxsize=RK3588_CFG["inference"]["buf_size"]
            )
            self._second_net_q_post = Queue(
                maxsize=RK3588_CFG["inference"]["buf_size"]
            )
            # Create obj for a second neural network
            self._second_net = NeuralNetwork(
                model=self._second_net_cfg["default_model"],
                q_in=self._second_net_q_pre,
                q_out=self._second_net_q_outs,
                core=RKNNLite.NPU_CORE_2
            )
            # Create inference process for a second neural network
            self._second_net_inf = Process(
                target = self._second_net.inference,
                daemon = True
            )
            # Create post process process for a second neural network
            self._second_net_post = Process(
                target = self._second_net_cfg.post_proc_func,
                kwargs = {
                    "q_in" : self._second_net_q_outs,
                    "q_out" : self._second_net_q_post
                },
                daemon=True
            )
            # Create camera obj
            self._cam = Cam(
                source=RK3588_CFG["camera"]["source"],
                nn_size=(
                    self._first_net_cfg["net_size"],
                    self._second_net_cfg["net_size"]
                ),
                q_in=(self._first_net_q_post, self._second_net_q_post),
                q_out=(self._first_net_q_pre, self._second_net_q_pre)
            )
        else:
            # Create camera obj
            self._cam = Cam(
                source=RK3588_CFG["camera"]["source"],
                nn_size=(self._first_net_cfg["net_size"],),
                q_in=(self._first_net_q_post,),
                q_out=(self._first_net_q_pre,)
            )
        # Create recording process
        self._rec = Process(
            target = self._cam.record,
            daemon=True
        )

    def start(self):
        self._rec.start()
        self._first_net_inf.start()
        self._first_net_post.start()
        if self._second_net_cfg is not None:
            self._second_net_inf.start()
            self._second_net_post.start()

    def show(self, start_time):
        self._cam.show(start_time)

    def get_data(self):
        # WIP
        return None
        # if self._q_post.empty():
        #     return None
        # raw_frame, inferenced_frame, detections, frame_id = self._q_post.get()
        # return(raw_frame, inferenced_frame, detections, frame_id)
