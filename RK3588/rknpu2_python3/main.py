from threading import Thread, Lock
from modules import storages as strgs
from modules.rk3588 import Rk3588
from modules.byte_tracker import BYTETracker, BTArgs
from modules.byte_tracker import tracking, draw_info, show


def fill_storages():
    global rk3588, raw_frames_storage, inferenced_frames_storage, detections_storage, lock
    while True:
        output = rk3588.get_data()
        if output is not None:
            with lock:
                raw_frame, frame, dets, frame_id = output
                raw_frames_storage.set_data(raw_frame)
                inferenced_frames_storage.set_data(frame)
                detections_storage.set_data(dets)


def bytetracker_draw():
    global inferenced_frames_storage, lock
    bytetrack_args = BTArgs()
    bytetracker = BYTETracker(bytetrack_args, frame_rate = 60)
    while True:
        dets = detections_storage.get_last_data()
        with lock:
            frame = inferenced_frames_storage.get_last_data()
        dets = tracking(
            bytetracker = bytetracker,
            dets = dets,
            frame_shape = frame.shape[:2]
        )
        if dets is not None:
            draw_info(
                frame = frame,
                dets = dets
            )
        show(frame)


def main():
    global rk3588, raw_frames_storage, inferenced_frames_storage, detections_storage, lock

    raw_frames_storage = strgs.ImageStorage(
        strgs.StoragePurpose.RAW_FRAME
    )
    inferenced_frames_storage = strgs.ImageStorage(
        strgs.StoragePurpose.INFERENCED_FRAME
    )
    detections_storage = strgs.DetectionsStorage()

    rk3588 = Rk3588()
    lock = Lock()

    strgs_thread = Thread(
        target = fill_storages,
        daemon = True
    )
    bytetracker_thread = Thread(
        target = bytetracker_draw,
        daemon = True
    )

    rk3588.start()
    strgs_thread.start()
    bytetracker_thread.start()

    while True:
        # rk3588.show()
        pass


if __name__ == "__main__":
    main()