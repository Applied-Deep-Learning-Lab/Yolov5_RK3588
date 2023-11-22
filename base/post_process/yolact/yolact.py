from multiprocessing import Queue

from base.post_process.yolact.utils.drawing import (after_nms_numpy,
                                                    get_anchors, nms_numpy,
                                                    permute, rknn_draw)
from log import DefaultLogger

# Create the inference's logger
logger = DefaultLogger("post_process")


def yolact_post_process(q_in: Queue, q_out: Queue) -> None:
    try:
        while True:
            outputs, raw_frame, frame_id = q_in.get()
            dets = None
            results = permute(outputs)
            anchors = get_anchors()
            results = nms_numpy(*results, anchors)
            results = after_nms_numpy(*results)
            frame = rknn_draw(raw_frame, *results)
            q_out.put((frame, raw_frame, dets, frame_id))

    except KeyboardInterrupt:
        logger.warning("Post process stopped by keyboard interrupt")
