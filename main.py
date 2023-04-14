import json
import time
from multiprocessing import Process
from pathlib import Path
from threading import Thread

import addons.storages as strgs
from addons.byte_tracker import BTArgs, BYTETracker
from addons.pulse_counter import Monitor
from addons.telegram_notifier import TelegramNotifier
from addons.webui import WebUI
from addons.webui.utils import obj_imgs_to_str
from base import Rk3588
from utils import do_counting, fill_storages, show_frames_localy

CONFIG_FILE = str(Path(__file__).parent.absolute()) + "/config.json"
with open(CONFIG_FILE, 'r') as config_file:
    cfg = json.load(config_file)


def main():
    """Runs inference and addons (if mentions)
    Creating storages and sending data to them
    """
    rk3588 = Rk3588()
    start_time = time.time()
    rk3588.start()
    if not cfg["storages"]["state"]:
        try:
            while True:
                rk3588.show(start_time)
        except Exception as e:
            print("Main exception: {}".format(e))
            exit()
    raw_frames_storage = strgs.ImageStorage(
        "raw frames"
    )
    inferenced_frames_storage = strgs.ImageStorage(
        "inferenced frames"
    )
    detections_storage = strgs.DetectionsStorage()
    counters_storage = strgs.Storage(
        storage_name="counters",
        data_size=(1,),
        data_amount=len(cfg["inference"]["classes"]),
        data_type=int
    )
    tracker = None
    if cfg["bytetrack"]["state"]:
        bytetrack_args = BTArgs()
        tracker = BYTETracker(
            args=bytetrack_args,
            frame_rate=cfg["bytetrack"]["fps"]
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
    if cfg["pulse_counter"]["state"]:
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
    if cfg["telegram_notifier"]["state"]:
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
            print("Bot exception: {}".format(e))
    if cfg["webui"]["state"]:
        ui = WebUI(
            raw_img_strg=raw_frames_storage,
            inf_img_strg=inferenced_frames_storage,
            dets_strg=detections_storage,
            counters_strg=counters_storage,
            camera=rk3588._cam
        )
        try:
            obj_imgs_to_str()
            ui.start()
        except Exception as e:
            print("WebUI exception: {}".format(e))
        finally:
            fill_thread.join()
            if cfg["pulse_counter"]["state"]:
                counting_thread.join() # type: ignore
            if cfg["telegram_notifier"]["state"]:
                notifier_process.join() # type: ignore
                notifier_process.close() # type: ignore
                notifier_process.kill() # type: ignore
            counters_storage.clear_buffer()
            raw_frames_storage.clear_buffer()
            inferenced_frames_storage.clear_buffer()
            detections_storage.clear_buffer()
            exit()
    try:
        show_frames_localy(
            inf_img_strg=inferenced_frames_storage,
            start_time=start_time
        )
    except Exception as e:
        print("Main exception: {}".format(e))
    finally:
        fill_thread.join()
        if cfg["pulse_counter"]["state"]:
            counting_thread.join() # type: ignore
        if cfg["telegram_notifier"]["state"]:
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
