import json
import math
import time
from multiprocessing import Value, shared_memory, resource_tracker
from pathlib import Path
from typing import Union

import numpy as np


CONFIG_FILE = str(Path(__file__).parent.parent.parent.absolute())+"/config.json"
with open(CONFIG_FILE, 'r') as config_file:
    cfg = json.load(config_file)


class Storage():
    """Class for creating numpy arrays that can share their data between
    processes/threads

    Args
    ---------------------------------------------------------------------------
    storage_name : StoragePurpose
        Describing storage purpose
    data_size : tuple
        Size of data stored (numpy array dimensionality)
    data_amount : int
        Amount of data stored
    data_type : type
        Type of stored data
    ---------------------------------------------------------------------------

    Attributes
    ---------------------------------------------------------------------------
    storage_name : StoragePurpose
        Describing storage purpose
    _buffer : multiprocessing.SharedMemory
        Shared memory buffer for set it as buf for storage(numpy array)
    _storage : np.ndarray
        Numpy array for stored data
    _index_counter : multiprocessing.Value
        Index of last stored data
    ---------------------------------------------------------------------------

    Methods
    ---------------------------------------------------------------------------
    set_data(data: np.ndarray) : None
        Set data to sharred numpy array
    def get_data_by_index(index: int) : np.ndarray
        Get data from sharred numpy array by index
    def get_last_data() : np.ndarray
        Get data from sharred numpy array by last index
    async def get_last_data_async() : np.ndarray
        Get data from sharred numpy array by last index for asynchronous call
    def get_last_index() : int
        Get last index of stored data in shared numpy array
    def clear_buffer() : None
        Clear shared memory buffers
    ---------------------------------------------------------------------------
    """
    def __init__(
            self,
            storage_name: str,
            data_size: tuple,
            data_amount: int,
            data_type: type
    ):
        self._DATA_AMOUNT=data_amount
        self._DELAY = cfg["storages"]["frames_delay"]
        self._index_counter = Value('i', 0)
        def _create_buffer(size, name):
            try:
                return shared_memory.SharedMemory(
                    create=True,
                    size=size,
                    name=name
                )
            except:
                return shared_memory.SharedMemory(
                    create=False,
                    size=size,
                    name=name
                )
        self.storage_name = storage_name
        self._buffer = _create_buffer(
            size=math.prod(
                (
                    math.prod(data_size),
                    self._DATA_AMOUNT,
                    np.dtype(data_type).itemsize
                )
            ),
            name=str(self.storage_name)
        )
        self._storage = np.ndarray(
            shape=(self._DATA_AMOUNT,) + data_size,
            dtype=data_type,
            buffer=self._buffer.buf
        )

    def set_data(
            self,
            data: Union[np.ndarray, int, None],
            id: int,
            start_time: float = 0
    ):
        data_index = id % self._DATA_AMOUNT # type: ignore
        if data is not None and type(data) == np.ndarray:
            self._storage[data_index][:len(data),:] = data
        else:
            self._storage[data_index][:] = data
        if cfg["debug"]["filled_frame_id"] and self.storage_name == 2:
            with open(cfg["debug"]["filled_id_file"], 'a') as f:
                f.write(
                    "{}\t{:.3f}\n".format(
                        data_index,
                        time.time() - start_time
                    )
                )
        self._index_counter.value += 1 # type: ignore

    def get_data_by_index(self, index: int):
        return self._storage[index][:]
    
    def get_last_data(self):
        data_index =\
            (self._index_counter.value - (self._DELAY + 1)) % self._DATA_AMOUNT # type: ignore
        return self._storage[data_index][:]
    
    async def get_last_data_async(self):
        data_index =\
            (self._index_counter.value - (self._DELAY + 1)) % self._DATA_AMOUNT # type: ignore
        return self._storage[data_index][:]

    def get_last_index(self):
        return(self._index_counter.value - (self._DELAY + 1)) # type: ignore

    def clear_buffer(self):
        # resource_tracker.unregister(f"{self._buffer.name}", "shared_memory")
        self._buffer.close()
        self._buffer.unlink()


class ImageStorage(Storage):
    """Child class of Storage class specifically for frames

    Attributes
    ---------------------------------------------------------------------------
    storage_name : StoragePurpose
        Describing storage purpose (raw or inferenced frames)
    ---------------------------------------------------------------------------
    """
    def __init__(self, storage_name: str):
        super().__init__(
            storage_name = storage_name,
            data_size = (cfg["camera"]["height"], cfg["camera"]["width"], 3),
            data_amount = cfg["storages"]["stored_data_amount"],
            data_type = np.uint8
        )


class DetectionsStorage(Storage):
    """Child class of Storage class specifically for detections numpy array"""
    def __init__(self):
        super().__init__(
            storage_name = "detections",
            data_size = (cfg["storages"]["dets_amount"], 6),
            data_amount = cfg["storages"]["stored_data_amount"],
            data_type = np.float32
        )