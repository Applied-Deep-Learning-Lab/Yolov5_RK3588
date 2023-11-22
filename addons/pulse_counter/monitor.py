import logging

import matplotlib.pyplot as plt

from config import RK3588_CFG
from log import DefaultLogger

from .utils import dets2cum_prob

logger = DefaultLogger(name="pulse_monitor", file_handler_level=logging.DEBUG)


class Monitor(object):

    def __init__(self, pos=320, size=20, switch_th=0.4):
        self.up_counter = 0
        self.down_counter = 0
        self.signal = 0
        self.switch_th = switch_th
        self.pos = pos
        self.size = size
        self._cum_prob = 0
        # Create a figure and axis for the real-time plot
        self._fig, self._ax = plt.subplots()
        self._ax.set_xlabel('Time (seconds)')
        self._ax.set_ylabel('cum_prob')
        self._ax.set_title('cum_prob over Time')
        self._x_data = []
        self._y_data = []
        self._line, = self._ax.plot(self._x_data, self._y_data, 'bo-')
        self._ax.grid(True)

    def update(self, dets):
        self.dets = dets
        self._cum_prob = dets2cum_prob(dets, self.pos, self.size)
        if RK3588_CFG["pulse_counter"]["log"] and self._cum_prob > 0.1:
            logger.debug(self._cum_prob)
        if self.signal == 1 and self._cum_prob < self.switch_th:
            self.signal = 0
            self.down_counter += 1
        elif self.signal == 0 and self._cum_prob > self.switch_th:
            self.signal = 1
            self.up_counter += 1

    def plot_graph(self, time):
        try:
            self._y_data.append(self._cum_prob)
            self._x_data.append(time)
            self._y_data = self._y_data[-50:]
            self._x_data = self._x_data[-50:]
            self._line.set_data(self._x_data, self._y_data)
            self._ax.relim()
            self._ax.autoscale_view()
            plt.pause(0.0001)
        except KeyboardInterrupt:
            logger.warning("Program stopped while plotting graph")
        except Exception as e:
            logger.error(f"Got exception - {e}")
            raise SystemExit
