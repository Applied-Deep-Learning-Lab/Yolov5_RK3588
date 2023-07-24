import logging
import os

import matplotlib.pyplot as plt

from config import RK3588_CFG

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
        self._cum_prob_values = []
        # Create a figure and axis for the real-time plot
        self._fig, self._ax = plt.subplots()
        self._ax.set_xlabel('Time')
        self._ax.set_ylabel('cum_prob')
        self._ax.set_title('cum_prob over Time')
        self._line, = self._ax.plot([], [], '-o')
        self._ax.grid(True)

    def update(self, dets):
        self.dets = dets
        cum_prob = dets2cum_prob(dets, self.pos, self.size)
        if RK3588_CFG["pulse_counter"]["log"] and cum_prob > 0.1:
            self._cum_prob_values.append(cum_prob)
            self._cum_prob_values = self._cum_prob_values[-500:]
            # Update the real-time plot
            self._line.set_data(range(len(self._cum_prob_values)), self._cum_prob_values)
            self._ax.relim()
            self._ax.autoscale_view()
        if self.signal == 1 and cum_prob < self.switch_th:
            self.signal = 0
            self.down_counter += 1
        elif self.signal == 0 and cum_prob > self.switch_th:
            self.signal = 1
            self.up_counter += 1

    def save_plot_as_image(self):
        # Finalize the plot before saving
        plt.ioff()
        plt.figure(self._fig.number) # type: ignore
        # Save the plot as an image
        plt.savefig(
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "log", "final_plot.png"
            )
        )
