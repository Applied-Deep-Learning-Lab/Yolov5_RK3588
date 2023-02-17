from modules import config
import numpy as np
from enum import IntEnum


class StoragePurpose(IntEnum):
    RAW_FRAME = 1
    INFERENCED_FRAME = 2
    DETECTIONS = 3


class Storage():
    def __init__(self, storage_name: StoragePurpose, data_size: tuple, data_amount: int, data_type: type):
        self._name = storage_name
        self._storage = np.ndarray((data_amount,) + data_size, dtype=data_type)
        self._index_counter = 0

    def __call__(self):
        self._index_counter += 1

    def set_data(self, data, index: int):
        self._storage[index][:] = data

    def get_data(self, index: int):
        return self._storage[index][:]


class ImageStorage(Storage):
    def __init__(self, storage_name: StoragePurpose):
        super().__init__(
            storage_name = storage_name,
            data_size = (config.CAM_HEIGHT, config.CAM_WIDTH, 3),
            data_amount = config.DATA_AMOUNT,
            data_type = np.uint8
        )


class DetectionsStorage(Storage):
    def __init__(self):
        super().__init__(
            storage_name = StoragePurpose.DETECTIONS,
            data_size = (6,),
            data_amount = config.DATA_AMOUNT,
            data_type = np.float64
        )