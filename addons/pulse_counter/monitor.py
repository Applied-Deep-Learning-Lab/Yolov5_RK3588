from .utils import dets2cum_prob

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
        if self.signal == 1 and cum_prob < self.switch_th:
            self.signal = 0
            self.down_counter += 1
        elif self.signal == 0 and cum_prob > self.switch_th:
            self.signal = 1
            self.up_counter += 1

        
