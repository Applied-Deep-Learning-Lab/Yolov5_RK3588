from utils import config
import numpy as np
from enum import IntEnum
from multiprocessing import shared_memory, Value
import math


class StoragePurpose(IntEnum):
    RAW_FRAME = 1
    INFERENCED_FRAME = 2
    DETECTIONS = 3


class Storage():
    def __init__(self, storage_name: StoragePurpose, data_size: tuple, data_amount: int, data_type: type):
        def _create_buffer(size, name):
            try:
                return shared_memory.SharedMemory(create=True, size=size, name=name)
            except:
                return shared_memory.SharedMemory(create=False, size=size, name=name)
        self.storage_name = storage_name
        self._buffer = _create_buffer(
            size = math.prod(
                (math.prod(data_size), data_amount, np.dtype(data_type).itemsize)
            ),
            name = str(self.storage_name)
        )
        self._storage = np.ndarray((data_amount,) + data_size, dtype=data_type, buffer=self._buffer.buf)
        self._index_counter = Value('i', 0)

    def set_data(self, data: np.ndarray):
        self._storage[self._index_counter.value % config.DATA_AMOUNT][:len(data),:] = data
        self._index_counter.value += 1

    def get_data(self, index: int):
        return self._storage[index][:]
    
    def get_last_index(self):
        return(self._index_counter.value - 1)


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