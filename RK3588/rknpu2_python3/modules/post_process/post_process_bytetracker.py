import numpy as np
import modules.post_process.rknn_post_process as rknn_pp


def post_process(lock, q_in, q_out):
    while True:
        outputs, frame, frame_id = q_in.get()
        data = list()
        for out in outputs:
            out = out.reshape([3, -1]+list(out.shape[-2:]))
            data.append(np.transpose(out, (2, 3, 0, 1)))
        boxes, classes, scores = rknn_pp.yolov5_post_process(data)
        dets = (boxes, classes, scores)
        raw_frame = frame.copy()
        if boxes is not None:
            rknn_pp.draw(frame, boxes, scores, classes)
        if q_out.full():
            continue
        with lock:
            q_out.put((frame, frame_id, raw_frame, dets))