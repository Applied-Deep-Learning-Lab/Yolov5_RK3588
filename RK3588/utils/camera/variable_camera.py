from utils import config
from utils.camera import Cam
from multiprocessing import Queue
import cv2

class VariableCamera(Cam):
    def __init__(self, source: int, q_in: Queue, q_out: Queue, q_settings: Queue):
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
                            self._cap.release()
                            self._cap = cv2.VideoCapture(settings[setting])
                            self._cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(*config.PIXEL_FORMAT))
                            continue
                        self._cap.set(int(setting), settings[setting])
                    print("Settings updated!")
                ret, frame = self._cap.read()
                raw_frame = frame.copy()
                if self._q_out.full():
                    continue
                frame = self._pre_process(frame)
                self._q_out.put((frame, raw_frame, self._frame_id))
                self._frame_id+=1
        finally:
            self._cap.release()