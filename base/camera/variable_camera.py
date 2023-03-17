import json
from multiprocessing import Queue
from pathlib import Path

import cv2

from base.camera import Cam


CONFIG_FILE = str(Path(__file__).parent.parent.parent.absolute()) + "/config.json"
with open(CONFIG_FILE, 'r') as config_file:
    cfg = json.load(config_file)


class VariableCamera(Cam):
    """Child class of Cam for reset camera settings while inference is running
    (without rebooting/restarting)

    Args
    ---------------------------------------------------------------------------
    source : int
        Camera index
    q_in : multiprocessing.Queue
        Queue that data reads from
    q_out : multiprocessing.Queue
        Queue that data sends to
    q_settings : multiprocessing.Queue
        Queue that camera settings reads from
    ---------------------------------------------------------------------------

    Attributes
    ---------------------------------------------------------------------------
    q_settings : multiprocessing.Queue
        Queue that camera settings reads from
    ---------------------------------------------------------------------------

    Methods
    ---------------------------------------------------------------------------
    record() : NoReturn
        Recordes raw frames, checking and updating settings
    ---------------------------------------------------------------------------
    """
    def __init__(
        self,
        source: int,
        q_in: Queue,
        q_out: Queue,
        q_settings: Queue
    ):
        super().__init__(
            source = source,
            q_in = q_in,
            q_out = q_out
        )
        self._q_settings = q_settings

    def record(self):
        if not self._cap.isOpened():
            print("Bad source")
        try:
            while True:
                if not self._q_settings.empty():
                    settings = self._q_settings.get()
                    for setting in settings:
                        if setting == 'source':
                            pixel_format = cfg["camera"]["pixel_format"]
                            self._cap.release()
                            self._cap = cv2.VideoCapture(settings[setting])
                            self._cap.set(
                                cv2.CAP_PROP_FOURCC,
                                cv2.VideoWriter.fourcc(*pixel_format)
                            )
                            continue
                        self._cap.set(int(setting), settings[setting])
                    print("Settings updated!")
                ret, frame = self._cap.read()
                raw_frame = frame.copy()
                if self._q_out.full():
                    continue
                frame = self._pre_process(frame) # type: ignore
                self._q_out.put((frame, raw_frame, self._frame_id))
                self._frame_id+=1
        finally:
            self._cap.release()