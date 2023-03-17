from multiprocessing import Queue

from rknnlite.api import RKNNLite

from base.inference import Yolov5


class VariableYolov5(Yolov5):
    """Child class of Yolov5 for reset model while inference is running
    (without rebooting/restarting)

    Args
    ---------------------------------------------------------------------------
    proc : int
        Number of running process for inference
    q_in : multiprocessing.Queue
        Queue that data reads from
    q_out : multiprocessing.Queue
        Queue that data sends to
    core : int
        Index of NPU core(s) that will be used for inference
        default (RKNNLite.NPU_CORE_AUTO) : sets all cores for inference 
        one frame
    ---------------------------------------------------------------------------

    Attributes
    ---------------------------------------------------------------------------
    q_model : multiprocessing.Queue
        Queue that new model reads from
    ---------------------------------------------------------------------------

    Methods
    ---------------------------------------------------------------------------
    inference() : NoReturn
        inference resized raw frames, checking and updating model
    ---------------------------------------------------------------------------
    """
    def __init__(
        self,
        proc: int,
        q_in: Queue,
        q_out: Queue,
        q_model: Queue,
        core: int = RKNNLite.NPU_CORE_AUTO
    ):
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