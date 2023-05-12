import json
import time
from datetime import datetime
from multiprocessing import Queue, Value
from pathlib import Path

import cv2
import numpy as np


ROOT = str(Path(__file__).parent.parent.parent.absolute()) + '/'
CONFIG_FILE = ROOT + "config.json"
with open(CONFIG_FILE, 'r') as config_file:
    cfg = json.load(config_file)
Mat = np.ndarray[int, np.dtype[np.generic]]


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
    def __init__(self, source: int, q_in: Queue, q_out: Queue):
        self._q_out = q_out
        self._q_in = q_in
        self._stop_record = Value('i', 0)
        self._source = source
        self._last_frame_id = 0
        self._frame_id = 0
        self._fps = 0
        self._max_fps = 0
        self._count = 0
        self._begin = 0

    def _pre_process(self, frame: Mat):
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame = cv2.resize(
            frame,
            (cfg["inference"]["net_size"], cfg["inference"]["net_size"])
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
            print("Bad source")
            raise SystemExit
        try:
            while not bool(self._stop_record.value): # type: ignore
                ret, frame = cap.read()
                if not ret:
                    print("Camera stopped!")
                    raise SystemExit
                raw_frame = frame.copy()
                frame = self._pre_process(frame)
                self._q_out.put((frame, raw_frame, self._frame_id))
                self._frame_id+=1
            cap.release()
        except Exception as e:
            print("Stop recording loop. Exception {}".format(e))
        finally:
            if cfg["debug"]["print_camera_release"]:
                message = "camera released - " +\
                    datetime.now().strftime('%Y-%m-%d.%H-%M-%S.%f') + "\n"
                with open(ROOT + cfg["debug"]["camera_release_file"], "a") as f:
                    f.write(message)
            cap.release()
            raise SystemExit

    def show(self, start_time):
        raw_frame, frame, dets, frame_id = self._q_in.get()
        self._count+=1
        if frame_id < self._last_frame_id:
            return
        if self._count % 30 == 0:
            self._fps = 30/(time.time() - self._begin)
            if self._fps > self._max_fps:
                self._max_fps = self._fps
            self._begin = time.time()

        frame = cv2.putText(
            img = frame,
            text = "id: {}".format(frame_id),
            org = (5, 30),
            fontFace = cv2.FONT_HERSHEY_SIMPLEX,
            fontScale = 1,
            color = (0,255,0), 
            thickness = 1,
            lineType = cv2.LINE_AA
        )
        frame = cv2.putText(
            img = frame,
            text = "fps: {:.2f}".format(self._fps),
            org = (5, 60),
            fontFace = cv2.FONT_HERSHEY_SIMPLEX,
            fontScale = 1,
            color = (0,255,0),
            thickness = 1,
            lineType = cv2.LINE_AA
        )
        frame = cv2.putText(
            img = frame,
            text = "max_fps: {:.2f}".format(self._max_fps),
            org = (5, 90),
            fontFace = cv2.FONT_HERSHEY_SIMPLEX,
            fontScale = 1,
            color = (0,255,0),
            thickness = 1,
            lineType = cv2.LINE_AA
        )
        cv2.imshow('frame', frame)
        self._last_frame_id = frame_id
        cv2.waitKey(1)
        if cfg["debug"]["showed_frame_id"]:
            with open(cfg["debug"]["showed_id_file"], 'a') as f:
                f.write(
                    "{}\t{:.3f}\n".format(
                        frame_id,
                        time.time() - start_time
                    )
                )

    def release(self):
        self._stop_record.value = 1 # type: ignore