import time
from multiprocessing import Process
from threading import Event, Thread

from base import Rk3588
from config import PIDNET_CFG, RK3588_CFG, YOLACT_CFG, YOLOV5_CFG
from log import DefaultLogger

if RK3588_CFG["bytetrack"]["state"]:
    from addons.byte_tracker import BTArgs, BYTETracker
if RK3588_CFG["pulse_counter"]["state"]:
    from addons.pulse_counter import Monitor
    from utils import do_counting
if RK3588_CFG["telegram_notifier"]["state"]:
    from addons.telegram_notifier import TelegramNotifier
if RK3588_CFG["storages"]["state"]:
    import addons.storages as strgs
    from utils import fill_storages, show_frames_localy
if RK3588_CFG["webui"]["state"] and RK3588_CFG["webui"]["server"] == "aiortc":
    from addons.webui.aiortc import WebUI
if RK3588_CFG["webui"]["state"] and RK3588_CFG["webui"]["server"] == "flask":
    from addons.webui.flask import WebUI

# Create the main's logger
logger = DefaultLogger("main")


def main():
    # Create list of the configs of the neural networks we want to run
    nets_cfgs=[YOLOV5_CFG]

    # Get program start time (for performance calculating)
    start_time = time.time()

    # Create and start core obj for inference
    try:
        rk3588 = Rk3588(
            nets_cfgs=nets_cfgs,
            start_time=start_time,
        )
    except KeyboardInterrupt:
        logger.warning("Program stopped by keyboard interrupt")
        exit()
    except SystemExit:
        logger.error(f"Program stopped by system exit")
        exit()
    except Exception as e:
        logger.error(f"Program stopped by {e}")
        exit()
    rk3588.start()

    # Start showing inferenced frames if we run more than one neural network
    if rk3588.dual_mode:
        try:
            while True:
                rk3588.show()
        except KeyboardInterrupt:
            logger.warning("Program stopped by keyboard interrupt")
        except Exception as e:
            logger.error(f"Main exception: {e}")
        finally:
            rk3588.stop()
            exit()
    # Run all enabled modules and show inferenced frames according to the selected method
    else:
        try:
            # Show inferenced frames without sync using storage (if storages module is disabled)
            if not RK3588_CFG["storages"]["state"]:
                while True:
                    rk3588.show()

            # Create event for stop threads
            stop_event = Event()
            # Create storages for sync and store various data
            # (raw images, inferenced images, detections on images, gps data, e.t.c)
            # Storage for raw images
            raw_frames_storage = strgs.ImageStorage("raw frames")  # type: ignore
            # Storage for inferenced images
            inferenced_frames_storage = strgs.ImageStorage(  # type: ignore
                storage_name="inferenced frames",
                start_time=start_time,
            )
            # Storage for detections from neural network
            detections_storage = strgs.DetectionsStorage()  # type: ignore

            # Update dettections storage for more specified options
            tracker = None
            # Check modules that can use detections storage
            dets_users_states = [
                RK3588_CFG["bytetrack"]["state"],
                RK3588_CFG["pulse_counter"]["state"]
            ]
            if sum(dets_users_states) > 1:
                logger.error("Please, choose only one detections storage user.")
                raise SystemExit
            # ByteTracker
            if RK3588_CFG["bytetrack"]["state"]:
                bytetrack_args = BTArgs()  # type: ignore
                tracker = BYTETracker(  # type: ignore
                    args=bytetrack_args,
                    frame_rate=RK3588_CFG["bytetrack"]["fps"]
                )
            # Pulse Monitor
            elif RK3588_CFG["pulse_counter"]["state"]:
                tracker = Monitor()  # type: ignore
                detections_storage = strgs.Storage(  # type: ignore
                    storage_name="counters",
                    data_size=(1,),
                    data_amount=len(nets_cfgs[0]["classes"]),
                    data_type=int,
                )

            # Create and run a thread that fills all storages with various data
            # (raw images, inferenced images, detections on images, gps data, e.t.c)
            fill_thread = Thread(
                target=fill_storages,  # type: ignore
                kwargs={
                    "stop_event": stop_event,
                    "rk3588": rk3588,
                    "tracker": tracker,
                    "raw_img_strg": raw_frames_storage,
                    "inf_img_strg": inferenced_frames_storage,
                    "dets_strg": detections_storage,
                },
                daemon=True
            )
            fill_thread.start()

            # Create and start process that sends counts of yolov5's detections
            if RK3588_CFG["telegram_notifier"]["state"]:
                # Checks if pulse counter is enabled
                if not RK3588_CFG["pulse_counter"]["state"]:
                    logger.error(
                        "Cannot run telegram notifier without pulse counter"
                    )
                    raise SystemExit
                telegram_notifier = TelegramNotifier(  # type: ignore
                    inf_img_strg=inferenced_frames_storage,
                    counters_strg=detections_storage,
                )
                notifier_process = Process(target=telegram_notifier.start)
                notifier_process.start()

            # Create and start WebUI that shows inferenced video and counts of yolov5's detections
            # (There are two versions of the WebUI (flask and aiortc), which are selectable by import one of them)
            if RK3588_CFG["webui"]["state"]:
                # TODO: Log that without YOLOV5 don't do request inference and
                # made counters_strg None as default
                if not RK3588_CFG["pulse_counter"]["state"]:
                    logger.error(
                        "Right now cannot run webui without pulse counter"
                    )
                    raise SystemExit
                webUI = WebUI(  # type: ignore
                    net_cfg=nets_cfgs[0],
                    raw_img_strg=raw_frames_storage,
                    dets_strg=detections_storage,  # type: ignore
                    inf_img_strg=inferenced_frames_storage,
                    counters_strg=detections_storage,
                )
                try:
                    webUI.start()
                except UnboundLocalError:
                    logger.error(
                        "Unavailable server: {}. Try 'flask' or 'aiortc'".format(
                        RK3588_CFG["webui"]["server"]
                        )
                    )
                except Exception as e:
                    logger.error(f"WebUI exception: {e}")
                finally:
                    raise SystemExit

            # Show synchronized inferenced video on the device if WebUI has not been selected
            show_frames_localy(  # type: ignore
                inf_img_strg=inferenced_frames_storage,
                start_time=start_time,
                stop_event=stop_event
            )
        except KeyboardInterrupt:
            logger.warning("Program stopped by keyboard interrupt")
        except SystemExit:
            logger.error(f"Program stopped by system exit")
        except Exception as e:
            logger.error(f"Program stopped by {type(e).__name__}")
        finally:
            rk3588.stop()
            if RK3588_CFG["storages"]["state"]:
                stop_event.set()  # type: ignore
            if RK3588_CFG["telegram_notifier"]["state"]:
                try:
                    notifier_process.terminate()  # type: ignore
                except UnboundLocalError:
                    logger.error("Telegram bot does not created")
            if RK3588_CFG["storages"]["state"]:
                try:
                    fill_thread.join(0.1)  # type: ignore
                except UnboundLocalError:
                    logger.warning(
                        "Thread hasn't been created to fill stores with data"
                    )
                raw_frames_storage.clear_buffer()  # type: ignore
                inferenced_frames_storage.clear_buffer()  # type: ignore
                detections_storage.clear_buffer()  # type: ignore
            exit()


if __name__ == "__main__":
    main()
