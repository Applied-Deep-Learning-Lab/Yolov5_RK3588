import numpy as np
from scipy.stats import norm

def check_width(l, r, min_width=16, max_width=128):
    if min_width <= r-l < max_width:
        return True
    else:
        return False


def filter_dets(dets, min_width=16, max_width=128):

    filtered = []
    for det in dets:
        l, t, r, b, cls_id, score = det
        if min_width <= r-l < max_width:
            filtered.append(det)

    return np.asarray(filtered)


def calc_occupied(dets):
    occupied = np.zeros(640)
    for det in dets:
        l, t, r, b, cls_id, score = det
        cx = int((l+r)/2)
        o_w = int(r - l)
        if score > 1:  # score in percents
            occupied[cx-o_w//4:cx+o_w//4] = score/100
        else:
            occupied[cx-o_w//4:cx+o_w//4] = score

    return occupied


def prob_fn(occupied, pos, size):
    xs = list(range(len(occupied)))
    xs = np.asarray(xs) - pos
    xs = xs.astype(np.float32)
    xs /= size/2
    return norm.pdf(xs) * 2/size * occupied


def cum_prob(occupied, pos, size):
    prob_dist = prob_fn(occupied, pos, size)
    return np.sum(prob_dist)

def dets2cum_prob(dets, pos=320, size=20):
    dets = filter_dets(dets)
    occupied = calc_occupied(dets)
    return cum_prob(occupied, pos, size)
