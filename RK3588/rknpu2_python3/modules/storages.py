from utils import config
import numpy as np
from enum import IntEnum


class StoragePurpose(IntEnum):
    RAW_FRAME = 1
    INFERENCED_FRAME = 2
    DETECTIONS = 3


class Storage():
    def __init__(self, storage_name: StoragePurpose, data_size: tuple, data_amount: int, data_type: type):
        self.storage_name = storage_name
        self._storage = np.ndarray((data_amount,) + data_size, dtype=data_type)
        self._index_counter = 0

    def set_data(self, data: np.ndarray):
        if data is not None:
            self._storage[self._index_counter % config.DATA_AMOUNT][:len(data),:] = data
        else:
            self._storage[self._index_counter % config.DATA_AMOUNT][:] = data
        self._index_counter += 1

    def get_data_by_index(self, index: int):
        return self._storage[index][:]
    
    def get_last_data(self):
        return self._storage[(self._index_counter - 1) % config.DATA_AMOUNT][:]
    
    def get_last_index(self):
        return(self._index_counter - 1)


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
            data_size = (config.NUM_DETS, 6),
            data_amount = config.DATA_AMOUNT,
            data_type = np.float32
        )