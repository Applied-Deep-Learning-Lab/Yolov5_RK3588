from multiprocessing import Queue

import cv2
import numpy as np

from log import DefaultLogger

# Create the inference's logger
logger = DefaultLogger("post_process")


def pidnet_post_process(q_in: Queue, q_out: Queue) -> None:
    try:
        while True:
            outputs, raw_frame, frame_id = q_in.get()
            dets = None
            # Prepare np.arrday for the cv2 manipulations
            result = np.swapaxes(outputs[0][0],0,2)
            result = np.swapaxes(result,0,1)
            result = (result*255).astype(np.uint8) # type: ignore
            result = cv2.resize(result, raw_frame.shape[-2::-1])
            # Create mask based on outputs and paste it on frame
            mask_colors = cv2.applyColorMap(result, cv2.COLORMAP_JET)
            frame = cv2.addWeighted(raw_frame, 0.5, mask_colors, 0.5, 0.0)
            q_out.put((frame, raw_frame, dets, frame_id))
    except KeyboardInterrupt:
        logger.warning("Post process stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Post process stopped by {e}")
        raise SystemExit
