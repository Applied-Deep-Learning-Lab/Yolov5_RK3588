from modules import config
import time
from modules.camera.camera import Cam

class VariableCamera(Cam):
    def __init__(self, source, lock, q_in, q_out, q_settings):
        super().__init_(
            source = source,
            lock = lock,
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
                        self._cap.set(setting, settings[setting])
                if config.PRINT_DIF:
                    start = time.time()
                ret, frame = self._cap.read()
                raw_frame = frame.copy()
                if self._q_out.full() or self._q_in.empty():
                    continue
                if config.PRINT_DIF:
                    print('r id(%d) - %f'%(self._frame_id, time.time() - start))
                if config.PRINT_TIME:
                    print('r id(%d) - %f'%(self._frame_id, time.time()))
                frame = self._pre_process(frame)
                if config.PRINT_DIF:
                    print('pr id(%d) - %f'%(self._frame_id, time.time() - start))
                if config.PRINT_TIME:
                    print('pr id(%d) - %f'%(self._frame_id, time.time()))
                with self._lock:
                    if config.PRINT_DIF:
                        self._q_out.put((frame, raw_frame, self._frame_id, start))
                    else:
                        self._q_out.put((frame, raw_frame, self._frame_id))
                    self._frame_id+=1
        finally:
            self._cap.release()