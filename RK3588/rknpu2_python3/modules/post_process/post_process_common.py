from modules import config
import numpy as np
import modules.post_process.rknn_post_process as rknn_pp
import time

def post_process(proc, q_in, q_out):
    while True:
        if config.PRINT_DIF:
            outputs, frame, frame_id, start = q_in.get()
        else:
            outputs, frame, frame_id = q_in.get()
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
        if q_out.full():
            continue
        if config.PRINT_DIF:
            q_out.put((frame, frame_id, start))
        else:
            q_out.put((frame, frame_id))