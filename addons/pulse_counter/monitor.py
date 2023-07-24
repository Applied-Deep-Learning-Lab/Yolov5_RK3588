import logging
import os

from .utils import dets2cum_prob

logger = logging.Logger("pulse_monitor")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "log", "pulse_monitor.log"
    )
)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter
formatter = logging.Formatter(
    fmt="[%(name)s] %(levelname)s - %(asctime)s: %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S"
)
handler.setFormatter(formatter)
logger.addHandler(handler)


class Monitor(object):

    def __init__(self, pos=320, size=20, switch_th=0.4):
        self.up_counter = 0
        self.down_counter = 0
        self.signal = 0
        self.switch_th = switch_th
        self.pos = pos
        self.size = size

    def update(self, dets):
        self.dets = dets
        cum_prob = dets2cum_prob(dets, self.pos, self.size)
        if cum_prob > 0.00001:
            logger.debug(cum_prob)
        if self.signal == 1 and cum_prob < self.switch_th:
            self.signal = 0
            self.down_counter += 1
        elif self.signal == 0 and cum_prob > self.switch_th:
            self.signal = 1
            self.up_counter += 1

        
