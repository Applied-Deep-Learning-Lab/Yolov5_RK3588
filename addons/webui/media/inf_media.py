import time
from fractions import Fraction
from timeit import default_timer as timer

from ..utils import draw_fps
import numpy as np
from aiortc import MediaStreamTrack
from av import VideoFrame

import addons.storages as strgs


class Statistics:
    def __init__(self):
        self.frameNum = 0
        self.frameDisplayTimes = []

    def registerFrame(self):
        self.frameNum += 1
        self.frameDisplayTimes.append(timer())

    def getFrameCount(self):
        return self.frameNum

    def getFps(self):
        times = self.frameDisplayTimes
        if len(times) <= 3:
            return 0
        if len(times) < 102:
            return (len(times) - 2) / (times[-1] - times[1])
        else:
            return 100 / (times[-1] - times[-101])


class InferenceTrack(MediaStreamTrack):
    """
    Track used to retrieve frames from Inference object
    """
    kind = "video"

    def __init__(
        self, inf_img_strg: strgs.ImageStorage,
        blank_frame: np.ndarray
    ):
        """
        InferenceTrack object initializer
            Parameters:
                inf(inference.Inference): Inference instance producing frames
            Returns:
                InferenceTrack class instance
        """
        super().__init__()
        self.stats = Statistics()
        self._inf_img_strg = inf_img_strg
        self._blank_frame = blank_frame
        self._begin = time.time()
        self._counter = 0
        self._fps = 0.0

    async def recv(self):
        """
        Redefined MediaStreamTrack.recv method to work with inference object
            Returns:
                new_frame(av.VideoFrame): formatted frame retrieved from
                inference object 
        """
        frame = await self._inf_img_strg.get_last_data_async()
        self._counter += 1
        if self._counter % 60 == 0:
            self._fps = 60 / (time.time() - self._begin)
            self._begin = time.time()
        frame = draw_fps(frame, self._fps)
        if not np.any(frame):
            frame = self._blank_frame
        new_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        new_frame.pts = int(self.stats.getFrameCount()) * 500
        new_frame.time_base = Fraction(1, 30000)
        self.stats.registerFrame()
        return new_frame

    def onClientShowedFrameInfo(self, frameNum):
        pass
