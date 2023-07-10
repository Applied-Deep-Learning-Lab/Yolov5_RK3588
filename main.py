import logging
import os
import time

from base import Rk3588
from config import PIDNET_CFG, RK3588_CFG, YOLACT_CFG, YOLOV5_CFG

# Create the main's logger
logger = logging.getLogger("main")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    os.path.join(
        os.path.dirname(__file__),
        "log/main.log"
    )
)
formatter = logging.Formatter(
    fmt="%(levelname)s - %(asctime)s: %(message)s.",
    datefmt="%d-%m-%Y %H:%M:%S"
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def main():
    rk3588 = Rk3588(
        first_net_cfg=YOLOV5_CFG,
        # second_net_cfg=PIDNET_CFG
    )
    start_time = time.time()
    rk3588.start()
    try:
        while True:
            rk3588.show(start_time)
    except Exception as e:
        logger.error(f"Main exception: {e}")
        exit()


if __name__ == "__main__":
    main()
