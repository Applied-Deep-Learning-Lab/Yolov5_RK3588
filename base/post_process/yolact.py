from multiprocessing import Queue


def yolact_post_process(q_in: Queue, q_out: Queue):
    while True:
        outputs, raw_frame, frame_id = q_in.get()
        # dets = None
        frame = raw_frame.copy()
        # Do some yolact postprocess
        q_out.put((raw_frame, frame, frame_id))