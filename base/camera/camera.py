import json
import logging
import os
import time
from datetime import datetime
from multiprocessing import Queue, Value
from pathlib import Path

import cv2
import numpy as np

ROOT = str(Path(__file__).parent.parent.parent.absolute())
CONFIG_FILE = ROOT + "/config.json"
with open(CONFIG_FILE, 'r') as config_file:
    cfg = json.load(config_file)
Mat = np.ndarray[int, np.dtype[np.generic]]

# Create the camera's logger
camera_logger = logging.getLogger("camera")
camera_logger.setLevel(logging.DEBUG)
camera_handler = logging.FileHandler(
    os.path.join(
        ROOT,
        "log/camera.log"
    )
)
camera_formatter = logging.Formatter(
    fmt="%(levelname)s - %(asctime)s: %(message)s.",
    datefmt="%d-%m-%Y %H:%M:%S"
)
camera_handler.setFormatter(camera_formatter)
camera_logger.addHandler(camera_handler)


class Cam():
    """Class for camera
    Sets camera settings, gets raw frames, shows inferenced frames (optional)

    Args
    ---------------------------------------------------------------------------
    source : int | str
        Camera index | path to a video
    q_in : multiprocessing.Queue
        Queue that data reads from
    q_out : multiprocessing.Queue
        Queue that data sends to
    ---------------------------------------------------------------------------

    Attributes
    ---------------------------------------------------------------------------
    _q_out : multiprocessing.Queue
        Queue that data sends to
    _q_in : multiprocessing.Queue
        Queue that data reads from
    _source : str
        Path to a video
    _last_frame_id : int
        Index of last showed frame
    _frame_id : int
        Index of recorded frame
    _fps : float
        Frames per second
    _count : int
        Counts all recorded frames
    _begin : float | int
        Start time of counting every 30 frames
    ---------------------------------------------------------------------------

    Methods
    ---------------------------------------------------------------------------
    _pre_process(frame: np.ndarray) : np.ndarray
        Resizing raw frames to net size
    record() : None
        Recordes raw frames
    show() : None
        Showes frames with bboxes
    ---------------------------------------------------------------------------
    """
    def __init__(
            self,
            source: int,
            nn_sizes: tuple[int, int],
            q_in: tuple[Queue, Queue],
            q_out: tuple[Queue, Queue]
    ):
        self._nn_sizes = nn_sizes
        self._q_out = q_out
        self._q_in = q_in
        self._stop_record = Value('i', 0)
        self._source = source
        self._last_frame_id = [0, 0]
        self._frame_id = 0
        self._fps = 0
        self._max_fps = 0
        self._count = 0
        self._begin = 0

    def _pre_process(self, frame: Mat, size: int):
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame = cv2.resize(
            frame,
            (size, size)
        )
        return frame

    def record(self):
        cap = cv2.VideoCapture(self._source)
        cap.set(
            cv2.CAP_PROP_FOURCC,
            cv2.VideoWriter.fourcc(*cfg["camera"]["pixel_format"])
        )
        cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            cfg["camera"]["width"]
        )
        cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            cfg["camera"]["height"]
        )
        cap.set(
            cv2.CAP_PROP_FPS,
            cfg["camera"]["fps"]
        )
        if(not cap.isOpened()):
            camera_logger.error("Bad source")
            raise SystemExit
        try:
            while not bool(self._stop_record.value): # type: ignore
                ret, frame = cap.read()
                if not ret:
                    camera_logger.error("Camera stopped!")
                    raise SystemExit
                raw_frame = frame.copy()
                # Pre process for each nn
                for i in range(len(self._q_out)):
                    frame = self._pre_process(frame, self._nn_sizes[i])
                    self._q_out[i].put((frame, raw_frame, self._frame_id))
                self._frame_id+=1
            cap.release()
        except Exception as e:
            camera_logger.error(f"Stop recording loop. Exception {e}")
        finally:
            camera_logger.error("Camera released.")
            cap.release()
            raise SystemExit

    def show(self, start_time):
        for i in range(len(self._q_in)):
            frame, raw_frame, frame_id = self._q_in[i].get()
            self._count+=1
            if frame_id < self._last_frame_id[i]:
                return
            if self._count % 30 == 0:
                self._fps = 30/(time.time() - self._begin)
                if self._fps > self._max_fps:
                    self._max_fps = self._fps
                self._begin = time.time()
            frame = cv2.putText(
                img = frame,
                text = "fps: {:.2f}".format(self._fps),
                org = (5, 30),
                fontFace = cv2.FONT_HERSHEY_SIMPLEX,
                fontScale = 1,
                color = (0,255,0),
                thickness = 1,
                lineType = cv2.LINE_AA
            )
            frame = cv2.putText(
                img = frame,
                text = "max_fps: {:.2f}".format(self._max_fps),
                org = (5, 60),
                fontFace = cv2.FONT_HERSHEY_SIMPLEX,
                fontScale = 1,
                color = (0,255,0),
                thickness = 1,
                lineType = cv2.LINE_AA
            )
            cv2.imshow(f'frame_{i}', frame)
            self._last_frame_id[i] = frame_id
            cv2.waitKey(1)
            # camera_logger.debug(f"{frame_id}\t{time.time() - start_time}")

    def release(self):
        self._stop_record.value = 1 # type: ignore
