from config import config_from_json
from pathlib import Path
import numpy as np
from enum import IntEnum
from multiprocessing import shared_memory, Value
import math


CONFIG_FILE = str(Path(__file__).parent.parent.parent.absolute()) + "/config.json"
cfg = config_from_json(CONFIG_FILE, read_from_file = True)


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
        if data is not None:
            self._storage[self._index_counter.value % cfg["storages"]["stored_data_amount"]][:len(data),:] = data
        else:
            self._storage[self._index_counter.value % cfg["storages"]["stored_data_amount"]][:] = data
        self._index_counter.value += 1

    def get_data_by_index(self, index: int):
        return self._storage[index][:]
    
    def get_last_data(self):
        return self._storage[(self._index_counter.value - 1) % cfg["storages"]["stored_data_amount"]][:]
    
    async def get_last_data_async(self):
        return self._storage[(self._index_counter.value - 1) % cfg["storages"]["stored_data_amount"]][:]

    def get_last_index(self):
        return(self._index_counter.value - 1)

    def clear_buffer(self):
        self._buffer.close()
        self._buffer.unlink()


class ImageStorage(Storage):
    def __init__(self, storage_name: StoragePurpose):
        super().__init__(
            storage_name = storage_name,
            data_size = (cfg["camera"]["height"], cfg["camera"]["width"], 3),
            data_amount = cfg["storages"]["stored_data_amount"],
            data_type = np.uint8
        )


class DetectionsStorage(Storage):
    def __init__(self):
        super().__init__(
            storage_name = StoragePurpose.DETECTIONS,
            data_size = (cfg["storages"]["dets_amount"], 6),
            data_amount = cfg["storages"]["stored_data_amount"],
            data_type = np.float32
        )