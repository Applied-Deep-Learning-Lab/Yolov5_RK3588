import logging
import os
import signal
import time
from multiprocessing import Process
from threading import Thread

from werkzeug.serving import make_server

import addons.storages as strgs
from addons.byte_tracker import BTArgs, BYTETracker
from addons.pulse_counter import Monitor
from addons.telegram_notifier import TelegramNotifier

# from addons.webui import WebUI
# from addons.webui.utils import obj_imgs_to_str

from addons.webui_flask import webUI_flask
from addons.webui_flask.utils import obj_imgs_to_str

from base import Rk3588
from config import PIDNET_CFG, RK3588_CFG, YOLACT_CFG, YOLOV5_CFG
from utils import do_counting, fill_storages, show_frames_localy

# Create the main's logger
logger = logging.getLogger("main")
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(
    os.path.join(
        os.path.dirname(__file__),
        "log/main.log"
    )
)
file_handler.setLevel(logging.ERROR)
formatter = logging.Formatter(
    fmt="%(levelname)s - %(asctime)s: %(message)s.",
    datefmt="%d-%m-%Y %H:%M:%S"
)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)


def signal_handler(signal, frame):
    logger.warning("Closing program.")
    exit()


def main():
    first_net_cfg = YOLOV5_CFG
    # second_net_cfg = PIDNET_CFG
    start_time = time.time()
    rk3588 = Rk3588(
        first_net_cfg=first_net_cfg,
        # second_net_cfg=second_net_cfg,
        start_time=start_time
    )
    rk3588.start()
    if rk3588.dual_mode:
        try:
            while True:
                rk3588.show()
        except Exception as e:
            logger.error(f"Main exception: {e}")
            exit()
    else:
        if not RK3588_CFG["storages"]["state"]:
            try:
                while True:
                    rk3588.show()
            except Exception as e:
                logger.error(f"Main exception: {e}")
                exit()
        raw_frames_storage = strgs.ImageStorage(
            "raw frames"
        )
        inferenced_frames_storage = strgs.ImageStorage(
            storage_name="inferenced frames",
            start_time=start_time
        )
        detections_storage = strgs.DetectionsStorage()
        counters_storage = strgs.Storage(
            storage_name="counters",
            data_size=(1,),
            data_amount=len(first_net_cfg["classes"]),
            data_type=int
        )
        tracker = None
        if RK3588_CFG["bytetrack"]["state"]:
            bytetrack_args = BTArgs()
            tracker = BYTETracker(
                args=bytetrack_args,
                frame_rate=RK3588_CFG["bytetrack"]["fps"]
            )
        fill_thread = Thread(
            target=fill_storages,
            kwargs={
                "rk3588": rk3588,
                "tracker": tracker,
                "raw_img_strg": raw_frames_storage,
                "inf_img_strg": inferenced_frames_storage,
                "dets_strg": detections_storage,
                "start_time": start_time
            },
            daemon=True
        )
        fill_thread.start()
        if RK3588_CFG["pulse_counter"]["state"]:
            pulse_monitor = Monitor()
            counting_thread = Thread(
                target=do_counting,
                kwargs={
                    "inf_img_strg": inferenced_frames_storage,
                    "dets_strg": detections_storage,
                    "counters_strg": counters_storage,
                    "pulse_monitor": pulse_monitor
                },
                daemon=True
            )
            counting_thread.start()
        if RK3588_CFG["telegram_notifier"]["state"]:
            telegram_notifier = TelegramNotifier(
                inf_img_strg=inferenced_frames_storage,
                counters_strg=counters_storage
            )
            notifier_process = Process(
                target=telegram_notifier.start,
                daemon=True
            )
            try:
                notifier_process.start()
            except Exception as e:
                logger.error(f"Bot exception: {e}")
        if RK3588_CFG["webui"]["state"]:

            webUI = webUI_flask(
                net_cfg=first_net_cfg,
                raw_img_strg=raw_frames_storage,
                dets_strg=detections_storage,
                inf_img_strg=inferenced_frames_storage,
                counters_strg=counters_storage
            )
            logger.info("Reading images for counter")
            obj_imgs_to_str()
            try:
                logger.info("Starting WebUI")
                server = make_server("0.0.0.0", 5000, webUI.app)
                server.serve_forever()
            except Exception as e:
                logger.error(f"WebUI exception: {e}")
            finally:
                fill_thread.join()
                if RK3588_CFG["pulse_counter"]["state"]:
                    counting_thread.join() # type: ignore
                if RK3588_CFG["telegram_notifier"]["state"]:
                    notifier_process.join() # type: ignore
                    notifier_process.close() # type: ignore
                    notifier_process.kill() # type: ignore
                counters_storage.clear_buffer()
                raw_frames_storage.clear_buffer()
                inferenced_frames_storage.clear_buffer()
                detections_storage.clear_buffer()
                exit()

            # ui = WebUI(
            #     raw_img_strg=raw_frames_storage,
            #     inf_img_strg=inferenced_frames_storage,
            #     dets_strg=detections_storage,
            #     counters_strg=counters_storage,
            #     camera=rk3588._cam,
            #     net_cfg=first_net_cfg
            # )
            # try:
            #     obj_imgs_to_str()
            #     ui.start()
            # except Exception as e:
            #     logger.error(f"WebUI exception: {e}")
            # finally:
            #     fill_thread.join()
            #     if RK3588_CFG["pulse_counter"]["state"]:
            #         counting_thread.join() # type: ignore
            #     if RK3588_CFG["telegram_notifier"]["state"]:
            #         notifier_process.join() # type: ignore
            #         notifier_process.close() # type: ignore
            #         notifier_process.kill() # type: ignore
            #     counters_storage.clear_buffer()
            #     raw_frames_storage.clear_buffer()
            #     inferenced_frames_storage.clear_buffer()
            #     detections_storage.clear_buffer()
            #     exit()

        try:
            show_frames_localy(
                inf_img_strg=inferenced_frames_storage,
                start_time=start_time
            )
        except Exception as e:
            logger.error(f"Main exception: {e}")
        finally:
            fill_thread.join()
            if RK3588_CFG["pulse_counter"]["state"]:
                counting_thread.join() # type: ignore
            if RK3588_CFG["telegram_notifier"]["state"]:
                notifier_process.join() # type: ignore
                notifier_process.close() # type: ignore
                notifier_process.kill() # type: ignore
            counters_storage.clear_buffer()
            raw_frames_storage.clear_buffer()
            inferenced_frames_storage.clear_buffer()
            detections_storage.clear_buffer()
            exit()


if __name__ == "__main__":
    main()
