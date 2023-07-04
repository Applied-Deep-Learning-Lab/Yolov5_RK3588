import json
import logging
import os
import time
from pathlib import Path

from base import Rk3588

CONFIG_FILE = str(Path(__file__).parent.absolute()) + "/config.json"
with open(CONFIG_FILE, 'r') as config_file:
    cfg = json.load(config_file)

# Create the main's logger
main_logger = logging.getLogger("main")
main_logger.setLevel(logging.DEBUG)
main_handler = logging.FileHandler(
    os.path.join(
        os.path.dirname(__file__),
        "log/main.log"
    )
)
main_formatter = logging.Formatter(
    fmt="%(levelname)s - %(asctime)s: %(message)s.",
    datefmt="%d-%m-%Y %H:%M:%S"
)
main_handler.setFormatter(main_formatter)
main_logger.addHandler(main_handler)


def main():
    rk3588 = Rk3588()
    start_time = time.time()
    rk3588.start()
    try:
        while True:
            rk3588.show(start_time)
    except Exception as e:
        main_logger.error(f"Main exception: {e}")
        exit()


if __name__ == "__main__":
    main()
