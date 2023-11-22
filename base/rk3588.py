from multiprocessing import Process, Queue
import time

from rknnlite.api import RKNNLite

from base.camera import Cam
from base.inference import NeuralNetwork
from config import RK3588_CFG, Config
from log import DefaultLogger

# Create the base's logger
logger = DefaultLogger("base")


class Rk3588():
    """Class for object detection on RK3588/RK3588S"""

    def __init__(
        self,
        nets_cfgs: list[Config],
        start_time: float = time.time(),
    ):
        # Set start time for calculating fps
        self._start_time = start_time

        # Get count of neural networks
        nn_count = len(nets_cfgs)

        # Check if cfg not setted
        if nn_count == 0:
            logger.error(
                "Please, choose which neural network(s) you want to run"
            )
            raise SystemExit
        # Set the mode as a single mode for informing other parts of the program
        elif nn_count == 1:
            logger.debug("Single mode")
            self.dual_mode = False
        # Set the mode as a multi mode for informing other parts of the program
        else:
            logger.debug("Multi mode")
            self.dual_mode = True

        # Set npu cores for each process (neural network)
        if nn_count == 2:
            cores = [
                RKNNLite.NPU_CORE_0_1,
                RKNNLite.NPU_CORE_2
            ]
        else:
            cores = [
                RKNNLite.NPU_CORE_0,
                RKNNLite.NPU_CORE_1,
                RKNNLite.NPU_CORE_2
            ]

        # Create queue for pre processing image
        q_pre = [
            Queue(
                maxsize=RK3588_CFG["inference"]["buf_size"]
            ) for _ in range(nn_count)
        ]
        # Create queue for inference's outputs
        q_outs = [
            Queue(
                maxsize=RK3588_CFG["inference"]["buf_size"]
            ) for _ in range(nn_count)
        ]
        # Create queue for post processing image
        self._q_post = [
            Queue(
                maxsize=RK3588_CFG["inference"]["buf_size"]
            ) for _ in range(nn_count)
        ]

        # Get neural network(s) size(s)
        nn_size = [
            cfg["net_size"]
            for cfg in nets_cfgs
        ]
        # Create camera object
        self._cam = Cam(
            source=RK3588_CFG["camera"]["source"],
            nn_size=nn_size,
            q_in=self._q_post,
            q_out=q_pre
        )

        # Create recording process
        self._rec = Process(
            target=self._cam.record,
            kwargs={
                "start_time": self._start_time
            }
        )

        # Create objects for neural networks
        neural_network = [
            NeuralNetwork(
                net_cfg=nets_cfgs[num % nn_count],
                q_in=q_pre[num % nn_count],
                q_out=q_outs[num % nn_count],
                core=core
            ) for num, core in zip(range(2 + abs(2 - nn_count)), cores)
        ]

        # Create inference processes for each neural network (processes)
        self._inference_process = [
            Process(
                target=neural_network[num].inference
            ) for num in range(2 + abs(2 - nn_count))
        ]

        # Create post process processes for each neural network (processes)
        self._post_process = [
            Process(
                target=nets_cfgs[num % nn_count].post_proc_func,
                kwargs={
                    "q_in": q_outs[num % nn_count],
                    "q_out": self._q_post[num % nn_count]
                }
            ) for num in range(2 + abs(2 - nn_count))
        ]

    def start(self):
        """
        Starts all processes (recording process, inference process(es),
        post_process process(es))
        """
        self._rec.start()
        for inference in self._inference_process: inference.start()
        for post_process in self._post_process: post_process.start()

    def stop(self):
        """
        Terminates all processes (recording process, inference process(es),
        post_process process(es))
        """
        self._rec.terminate()
        for inference in self._inference_process: inference.terminate()
        for post_process in self._post_process: post_process.terminate()

    def show(self):
        """
        Create cv2 window with inferenced frames (frames with bboxes on them)
        """
        self._cam.show(self._start_time)

    def get_data(self):
        """
        Returns raw frames, frames with bboxes, numpy array with detections
        and frames ids
        """
        data = [
            (q.get()) # inf_frame, raw_frame, dets, frame_id
            for q in self._q_post
        ]
        return data
