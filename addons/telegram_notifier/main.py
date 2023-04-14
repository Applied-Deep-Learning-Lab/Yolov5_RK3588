import asyncio
import json
import os
import time
import traceback
from datetime import datetime
from pathlib import Path

import cv2
from telegram import Bot
from telegram.error import BadRequest

import addons.storages as strgs

CONFIG_FILE = str(
    Path(__file__).parent.parent.parent.absolute()) + "/config.json"
with open(CONFIG_FILE, 'r') as config_file:
    cfg = json.load(config_file)


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
        self._TOKEN = cfg["telegram_notifier"]["token"]
        self._CHAT_ID = cfg["telegram_notifier"]["chat_id"]
        try:
            self._bot = Bot(token=self._TOKEN)
            self._start = datetime.now().strftime('%H:%M:%S %d.%m.%Y')
        except Exception as e:
            print("Can't start bot: {}".format(e))
            return
        self._counters_strg = counters_strg
        self._hostname = os.uname()[1]
        self._classes = cfg["inference"]["classes"]
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
        self._time_period = cfg["telegram_notifier"]["time_period"]
        self._last_counters = [0] * len(self._classes)
        print("Bot is ready")

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
                    )
                    sent = True
                except BadRequest:
                    await self._bot.send_photo(
                        chat_id=self._CHAT_ID,
                        photo=img.tobytes()
                    )
                    await self._bot.send_message(
                        chat_id=self._CHAT_ID,
                        text=caption
                    )
                    sent = True
                except:
                    retries_left -= 1
                    time.sleep(1)
                    print(traceback.format_exc())
