from multiprocessing import Queue

import numpy as np

from base.post_process.yolov5.utils import draw, process_yolov5_output
from base.utils import format_dets
from log import DefaultLogger

# Create the inference's logger
logger = DefaultLogger("post_process")


def yolov5_post_process(q_in: Queue, q_out: Queue):
    """Overlays bboxes on frames

    Args
    -----------------------------------
    q_in : multiprocessing.Queue
        Queue that data reads from
    q_out : multiprocessing.Queue
        Queue that data sends to
    -----------------------------------
    """
    try:
        while True:
            outputs, raw_frame, frame_id = q_in.get()
            frame = raw_frame.copy()
            dets = None
            data = list()
            for out in outputs:
                out = out.reshape([3, -1]+list(out.shape[-2:]))
                data.append(np.transpose(out, (2, 3, 0, 1)))
            boxes, classes, scores = process_yolov5_output(data)
            if boxes is not None:
                draw(frame, boxes, scores, classes)
                dets = format_dets(
                    boxes = boxes,
                    classes = classes, # type: ignore
                    scores = scores # type: ignore
                )
            q_out.put((frame, raw_frame, dets, frame_id))
    except KeyboardInterrupt:
        logger.warning("Post process stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Post process stopped by {e}")
        raise SystemExit
