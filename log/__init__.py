import os
import logging
import time


class TimestampFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        timestamp_ns = time.time_ns()
        timestamp_seconds = timestamp_ns // 1_000_000_000
        formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp_seconds))
        return f"{formatted_time} ({timestamp_ns})"


class TimestampLogger(logging.Logger):
    def __init__(
        self,
        name: str,
        level: int = logging.DEBUG
    ):
        super().__init__(name=name, level=level)
        formatter = TimestampFormatter(
            fmt="[%(name)s] %(levelname)s - %(asctime)s: %(message)s.",
            datefmt="%d-%m-%Y %H:%M:%S",
        )
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        self.addHandler(console_handler)
        file_handler = logging.FileHandler(
            os.path.join(os.path.dirname(__file__), f"{name}.log")
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.addHandler(file_handler)


class DefaultLogger(logging.Logger):
    def __init__(
        self,
        name: str,
        level: int = logging.DEBUG,
        console_handler_level: int = logging.DEBUG,
        create_file_handler: bool = True,
        file_handler_level: int = logging.WARNING,
    ):
        super().__init__(name=name, level=level)
        formatter = logging.Formatter(
            fmt="[%(name)s] %(levelname)s - %(asctime)s: %(message)s.",
            datefmt="%d-%m-%Y %H:%M:%S",
        )
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_handler_level)
        console_handler.setFormatter(formatter)
        self.addHandler(console_handler)
        if create_file_handler:
            file_handler = logging.FileHandler(
                os.path.join(os.path.dirname(__file__), f"{name}.log")
            )
            file_handler.setLevel(file_handler_level)
            file_handler.setFormatter(formatter)
            self.addHandler(file_handler)
