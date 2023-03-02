from threading import Thread
from modules import storages
from modules.rk3588 import Rk3588


def main():
    raw_frames_storage = storages.ImageStorage(
        storages.StoragePurpose.RAW_FRAME
    )
    inferenced_frames_storage = storages.ImageStorage(
        storages.StoragePurpose.INFERENCED_FRAME
    )
    detections_storage = storages.DetectionsStorage()
    rk3588 = Rk3588()
    rk3588.start()
    try:
        while True:
            # Debug print
            # print(detections_storage.get_data(0)[0])
            rk3588.show()
    finally:
        raw_frames_storage.clear_buffer()
        inferenced_frames_storage.clear_buffer()
        detections_storage.clear_buffer()


if __name__ == "__main__":
    main()