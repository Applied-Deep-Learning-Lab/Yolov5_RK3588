from multiprocessing import Queue
import cv2
import numpy as np

def pidnet_post_process(q_in: Queue, q_out: Queue):
    while True:
        outputs, raw_frame, frame_id = q_in.get()
        # dets = None
        # Prepare np.arrday for the cv2 manipulations
        result = np.swapaxes(outputs[0][0],0,2)
        result = np.swapaxes(result,0,1)
        result = (result*255).astype(np.uint8)
        # Create mask based on outputs and paste it on frame
        mask_colors = cv2.applyColorMap(result, cv2.COLORMAP_JET)
        frame = cv2.resize(raw_frame, (768, 768))
        frame = cv2.addWeighted(frame, 0.5, mask_colors, 0.5, 0.0)
        q_out.put((frame, raw_frame, frame_id))