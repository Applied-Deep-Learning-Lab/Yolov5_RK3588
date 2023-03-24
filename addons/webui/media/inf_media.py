from aiortc import MediaStreamTrack
from av import VideoFrame
from fractions import Fraction
from timeit import default_timer as timer
import addons.storages as strgs
import numpy as np


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
        self._cur_id = 0
        self._last_id = 0
        self._blank_frame = blank_frame

    async def recv(self):
        """
        Redefined MediaStreamTrack.recv method to work with inference object
            Returns:
                new_frame(av.VideoFrame): formatted frame retrieved from
                inference object 
        """
        while not self._cur_id > self._last_id:
            frame, self._cur_id = await self._inf_img_strg.get_last_data_async()
        if not np.any(frame):
            frame = self._blank_frame
        new_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        new_frame.pts = int(self.stats.getFrameCount()) * 500
        new_frame.time_base = Fraction(1, 30000)
        self.stats.registerFrame()
        self._last_id = self._cur_id
        return new_frame

    def onClientShowedFrameInfo(self, frameNum):
        pass
