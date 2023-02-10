from modules import config
import numpy as np
from modules import rkkn_post_process as rknn_pp
import time

def post_process(proc, lock, q_outs, q_post):
    while True:
        if config.PRINT_DIF:
            outputs, frame, frame_id, start = q_outs.get()
        else:
            outputs, frame, frame_id = q_outs.get()
        data = list()
        for out in outputs:
            out = out.reshape([3, -1]+list(out.shape[-2:]))
            data.append(np.transpose(out, (2, 3, 0, 1)))
        boxes, classes, scores = rknn_pp.yolov5_post_process(data)
        if boxes is not None:
            rknn_pp.draw(frame, boxes, scores, classes)
        if config.PRINT_DIF:
            print('po%d id(%d) - %f'%(proc, frame_id, time.time() - start))
        if config.PRINT_TIME:
            print('po%d id(%d) - %f'%(proc, frame_id, time.time()))
        if q_post.full():
            continue
        with lock:
            if config.PRINT_DIF:
                q_post.put((frame, frame_id, start))
            else:
                q_post.put((frame, frame_id))