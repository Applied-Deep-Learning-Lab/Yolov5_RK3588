import asyncio
import json
import logging
import os
import time
import traceback
from datetime import datetime

import cv2
import httpx
from telegram import Bot
from telegram.error import BadRequest

import addons.storages as strgs
from config import RK3588_CFG, YOLOV5_CFG

# Create the tg_bot's logger
tg_bot_logger = logging.Logger("tg_bot")
tg_bot_logger.setLevel(logging.DEBUG)
# Create handler that output all info to the console
tg_bot_console_handler = logging.StreamHandler()
tg_bot_console_handler.setLevel(logging.DEBUG)
# Create handler that output errors, warnings to the file
tg_bot_file_handler = logging.FileHandler(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "log/tg_bot.log"
    )
)
tg_bot_file_handler.setLevel(logging.ERROR)
# Create formatter for handlers
tg_bot_formatter = logging.Formatter(
    fmt="%(levelname)s - %(asctime)s: %(message)s.",
    datefmt="%d-%m-%Y %H:%M:%S"
)
tg_bot_console_handler.setFormatter(tg_bot_formatter)
tg_bot_file_handler.setFormatter(tg_bot_formatter)
# Add handlers to the logger
tg_bot_logger.addHandler(tg_bot_console_handler)
tg_bot_logger.addHandler(tg_bot_file_handler)



class TelegramNotifier():
    """Class for telegram bot notifier that sends inferenced frames to
    channel/group every x seconds (x sets in args)
    Args
    ---------------------------------------------------------------------------
    inf_img_strg : storages.ImageStorage
        Object of ImageStorage that stored inferenced frames
    ---------------------------------------------------------------------------

    Attributes
    ---------------------------------------------------------------------------
    _TOKEN: str
        Telegram bot token
    _CHAT_ID: str|int
        Telegram's group/channel chat_id
    _bot: telegram.Bot
        Telegram bot
    _hostname: str
        Host machine name
    _counters: dict[str, float, str]
        Dict with hostname, bot launch time, image send time
        This is necessary to attach to the sent image
    _inf_img_strg : storages.ImageStorage
        Object of ImageStorage that stored inferenced frames
    _time_period: int
        Period in which time the inferenced frames will be sent (in seconds)
    ---------------------------------------------------------------------------

    Methods
    ---------------------------------------------------------------------------
    start(): None
        Starts the telegram bot notifier
    _notificate(): NoReturn
        Sends notification (inferenced image and description dict) to the
        telegram channel/group
    ---------------------------------------------------------------------------
    """

    def __init__(
            self,
            inf_img_strg: strgs.ImageStorage,
            counters_strg: strgs.Storage
        ):
        self._TOKEN = RK3588_CFG["telegram_notifier"]["token"]
        self._CHAT_ID = RK3588_CFG["telegram_notifier"]["chat_id"]
        try:
            self._bot = Bot(token=self._TOKEN)
            self._start = datetime.now().strftime('%H:%M:%S %d.%m.%Y')
        except Exception as e:
            tg_bot_logger.error(f"Can't start bot: {e}")
            return
        self._counters_strg = counters_strg
        self._hostname = os.uname()[1]
        self._classes = YOLOV5_CFG["classes"]
        self._caption = {
            "hostname": self._hostname,
            "start_time": self._start,
            "current_time": datetime.now().strftime('%H:%M:%S %d.%m.%Y'),
            "count": {
                self._classes[i]: int(self._counters_strg.get_data_by_index(i))
                for i in range(len(self._classes))
                if int(self._counters_strg.get_data_by_index(i)) != 0
            }
        }
        self._inf_img_strg = inf_img_strg
        self._time_period = RK3588_CFG["telegram_notifier"]["time_period"]
        self._last_counters = [0] * len(self._classes)
        tg_bot_logger.info("Bot is ready")

    def start(self):
        notificate_loop = asyncio.get_event_loop()
        notificate_loop.run_until_complete(self._notificate())

    async def _notificate(self):
        while True:
            begin = time.time()
            while time.time() - begin < self._time_period:
                pass
            self._caption["current_time"] =\
                datetime.now().strftime('%H:%M:%S %d.%m.%Y')
            try:
                self._caption["count"] = {
                    self._classes[i]:\
                        int(self._counters_strg.get_data_by_index(i)) -\
                            self._last_counters[i]
                    for i in range(len(self._classes))
                    if int(self._counters_strg.get_data_by_index(i)) != 0
                }
                for i in range(len(self._classes)):
                    self._last_counters[i] =\
                        int(self._counters_strg.get_data_by_index(i))
            except:
                tg_bot_logger.warning("Counting troubles.")
                self._caption["count"] = "counting troubles"
            caption = json.dumps(
                obj=self._caption,
                indent=4
            )
            img = self._inf_img_strg.get_last_data()
            ret, img = cv2.imencode('.jpg', img)
            sent = False
            retries_left = 5
            while not sent and retries_left:
                try:
                    await self._bot.send_photo(
                        chat_id=self._CHAT_ID,
                        photo=img.tobytes(),
                        caption=caption
                    ) # type: ignore
                    sent = True
                except BadRequest:
                    await self._bot.send_photo(
                        chat_id=self._CHAT_ID,
                        photo=img.tobytes()
                    ) # type: ignore
                    await self._bot.send_message(
                        chat_id=self._CHAT_ID,
                        text=caption
                    ) # type: ignore
                    sent = True
                except httpx.ReadTimeout:
                    retries_left -= 1
                    time.sleep(1)
                    print("Connection pool timeout. Retrying...")
                except:
                    retries_left -= 1
                    time.sleep(1)
                    tg_bot_logger.warning(traceback.format_exc())
