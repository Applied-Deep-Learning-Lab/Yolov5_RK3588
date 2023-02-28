import cv2
import time
from modules import config

class Cam():
    def __init__(self, source, q_in, q_out):
        self._q_out = q_out
        self._q_in = q_in
        self._cap = cv2.VideoCapture(source)
        self._cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(*config.PIXEL_FORMAT))
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAM_WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAM_HEIGHT)
        self._cap.set(cv2.CAP_PROP_FPS, config.CAM_FPS)
        self._frame_id = 0
        self._fps = 0
        self._max_fps = 0
        self._count = 0
        self._begin = 0

    def _pre_process(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame = cv2.resize(frame, (config.NET_SIZE, config.NET_SIZE))
        return frame

    def record(self):
        if(not self._cap.isOpened()):
            print("Bad source")
        ret, frame = self._cap.read()
        try:
            while ret:
                if config.PRINT_DIF:
                    start = time.time()
                ret, frame = self._cap.read()
                raw_frame = frame.copy()
                if self._q_out.full():
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
                if config.PRINT_DIF:
                    self._q_out.put((frame, raw_frame, self._frame_id, start))
                else:
                    self._q_out.put((frame, raw_frame, self._frame_id))
                self._frame_id+=1
        finally:
            self._cap.release()

    def show(self):
        if self._q_in.empty():
            return
        self._count+=1
        if config.PRINT_DIF:
            frame, frame_id, start = self._q_in.get()
        else:
            frame, frame_id = self._q_in.get()
        # FPS COUNTER
        if not self._count % 30:
            self._fps = 30/(time.time() - self._begin)
            if self._fps > self._max_fps:
                self._max_fps = self._fps
            self._begin = time.time()

        frame = cv2.putText(frame, f"id: {frame_id}", (5, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 1, cv2.LINE_AA)
        frame = cv2.putText(frame, "fps: %.2f"%(self._fps), (5, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 1, cv2.LINE_AA)
        frame = cv2.putText(frame, f"max_fps: {self._max_fps}", (5, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 1, cv2.LINE_AA)

        # Debug
        if config.PRINT_IDS:
            with open(config.FRAMES_IDS_FILE, 'a') as f:
                f.write(str(frame_id)+'\n')

        cv2.imshow('frame', frame)
        if config.PRINT_DIF:
            print('s id(%d) - %f'%(frame_id, time.time() - start))
        if config.PRINT_TIME:
            print('s id(%d) - %f'%(frame_id, time.time()))
        cv2.waitKey(1)

    async def get_frame(self):
        self._count+=1
        frame, frame_id = self._q_in.get()
        if not self._count % 30:
            self._fps = 30/(time.time() - self._begin)
            if self._fps > self._max_fps:
                self._max_fps = self._fps
            self._begin = time.time()
        frame = cv2.putText(frame, f"id: {frame_id}", (5, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 1, cv2.LINE_AA)
        frame = cv2.putText(frame, "fps: %.2f"%(self._fps), (5, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 1, cv2.LINE_AA)
        frame = cv2.putText(frame, f"max_fps: {self._max_fps}", (5, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 1, cv2.LINE_AA)
        return frame