import logging
import math
import time
from multiprocessing import Value, shared_memory
from typing import Union

import numpy as np

from config import RK3588_CFG
from log import DefaultLogger

# Create loggers
set_logger = DefaultLogger(name="set_storages", file_handler_level=logging.DEBUG)
get_logger = DefaultLogger(name="get_storages", file_handler_level=logging.DEBUG)


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
            data_type: type,
            start_time: float = time.time()
    ):
        self._start_time = start_time
        self._DATA_AMOUNT=data_amount
        self._DELAY = RK3588_CFG["storages"]["frames_delay"]
        self._index_counter = Value('i', 0)
        # for fps
        if RK3588_CFG["count_fps"]:
            self._set_last_frame_time = time.time()
            self._set_frames_count = 0
            self._get_last_frame_time = time.time()
            self._get_frames_count = 0
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
            id: int
    ):
        data_index = id % self._DATA_AMOUNT # type: ignore
        if data is not None and type(data) == np.ndarray:
            self._storage[data_index][:len(data),:] = data
        else:
            self._storage[data_index][:] = data
        if RK3588_CFG["debug"] and "inf" in self.storage_name:
            set_logger.debug(
                "set:\t{}\t{}".format(
                    data_index,
                    time.time() - self._start_time
                )
            )
        if RK3588_CFG["count_fps"]:
            self._set_frames_count += 1
            if self._set_frames_count % 30 == 0:
                set_logger.debug(
                    f"{30/(time.time() - self._set_last_frame_time):.2f}"
                )
                self._set_last_frame_time = time.time()
        self._index_counter.value += 1 # type: ignore

    def get_data_by_index(self, index: int):
        return self._storage[index][:]
    
    def get_last_data(self):
        data_index =\
            (self._index_counter.value - (self._DELAY + 1)) % self._DATA_AMOUNT # type: ignore
        if RK3588_CFG["count_fps"] and "inf" in self.storage_name:
            self._get_frames_count += 1
            if self._get_frames_count % 30 == 0:
                get_logger.debug(
                    f"{30/(time.time() - self._get_last_frame_time):.2f}"
                )
                self._get_last_frame_time = time.time()
        if RK3588_CFG["debug"] and "inf" in self.storage_name:
            get_logger.debug(
                "get:\t{}\t{}".format(
                    data_index,
                    time.time() - self._start_time
                )
            )
        return self._storage[data_index][:]
    
    async def get_last_data_async(self):
        data_index =\
            (self._index_counter.value - (self._DELAY + 1)) % self._DATA_AMOUNT # type: ignore
        if RK3588_CFG["count_fps"] and "inf" in self.storage_name:
            self._get_frames_count += 1
            if self._get_frames_count % 30 == 0:
                get_logger.debug(
                    f"{30/(time.time() - self._get_last_frame_time):.2f}"
                )
                self._get_last_frame_time = time.time()
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
    def __init__(
            self,
            storage_name: str,
            size: Union[tuple[int, int], None] = None,
            start_time: float = time.time()
    ):
        if size is None:
            height = RK3588_CFG["camera"]["height"]
            width = RK3588_CFG["camera"]["width"]
        else:
            height, width = size
        super().__init__(
            storage_name = storage_name,
            data_size = (height, width, 3),
            data_amount = RK3588_CFG["storages"]["stored_data_amount"],
            data_type = np.uint8,
            start_time=start_time
        )


class DetectionsStorage(Storage):
    """Child class of Storage class specifically for detections numpy array"""
    def __init__(self):
        super().__init__(
            storage_name = "detections",
            data_size = (RK3588_CFG["storages"]["dets_amount"], 6),
            data_amount = RK3588_CFG["storages"]["stored_data_amount"],
            data_type = np.float32
        )