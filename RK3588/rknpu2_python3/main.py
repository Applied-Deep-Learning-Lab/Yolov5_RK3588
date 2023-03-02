from threading import Thread
from utils import storages as strgs
from modules.OrangePi import OrangePi


def main():
    raw_frames_storage = strgs.ImageStorage(
        strgs.StoragePurpose.RAW_FRAME
    )
    inferenced_frames_storage = strgs.ImageStorage(
        strgs.StoragePurpose.INFERENCED_FRAME
    )
    detections_storage = strgs.DetectionsStorage()
    storages = [
        raw_frames_storage,
        inferenced_frames_storage,
        detections_storage
    ]
    orange_pi = OrangePi(storages)
    orange_pi.start()
    while True:
        # Debug print
        print(detections_storage.get_data(0)[0])
        orange_pi.show()


if __name__ == "__main__":
    main()