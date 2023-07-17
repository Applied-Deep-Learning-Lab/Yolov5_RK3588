import json
import logging
import os

import psutil
from flask import Flask, Response, jsonify, render_template, request

from addons.storages import ImageStorage, Storage
from addons.webui_flask.utils import gen_frame
from config import RK3588_CFG, Config

logger = logging.getLogger("server")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "log", "server.log"
    )
)
formatter = logging.Formatter(
    fmt="[%(name)s] %(levelname)s - %(asctime)s: %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S"
)
handler.setFormatter(formatter)
logger.addHandler(handler)


class webUI_flask():
    def __init__(
            self,
            net_cfg: Config,
            inf_img_strg: ImageStorage,
            counters_strg: Storage
    ):
        self._ROOT = os.path.dirname(__file__)
        self._inf_img_strg = inf_img_strg
        self._counters_strg = counters_strg
        self._net_cfg = net_cfg
        self._classes = net_cfg["classes"]
        self.app = Flask(__name__)
        # self.app.json.sort_keys = False

        @self.app.route('/')
        def home_page() -> str:
            return render_template("home.html")


        @self.app.route('/settings/')
        def settings_page() -> str:
            return render_template(
                'settings.html',
                base_cfg=RK3588_CFG,
                net_cfg=self._net_cfg
            )

        @self.app.route('/settings_values')
        def settings_send():
            settings = {
                "base": RK3588_CFG,
                "neural_network": self._net_cfg
            }
            return jsonify(settings)

        @self.app.route('/settings_values', methods=["POST"])
        def settings_get() -> Response:
            try:
                settings = request.json
            except Exception as e:
                logger.error(f"Update settings exceptions: {e}.")
                return jsonify(
                    {'message': f'Get some troubles with updating settings.\n{e}'}
                )
            if settings is None:
                logger.warning("Didn't get anything about the settings.")
                return jsonify(
                    {"message": "Didn't get anything about the settings."}
                )
            # Action
            RK3588_CFG.update(settings["base"])
            self._net_cfg.update(settings["neural_network"])
            RK3588_CFG.upload()
            self._net_cfg.upload()
            return jsonify({"message": "Settings updated."})

        @self.app.route('/video_feed')
        def video_feed() -> Response:
            return Response(
                response=gen_frame(
                    self._inf_img_strg
                ),
                mimetype='image/jpeg'
            )
        
        @self.app.route('/cpu_temperature')
        def set_temperature() -> Response:
            return jsonify(
                psutil.sensors_temperatures()["center_thermal"][0][1]
            )

        @self.app.route('/counters_data')
        def set_counters() -> Response:
            counters = {
                self._classes[i]: int(self._counters_strg.get_data_by_index(i)) # type: ignore
                for i in range(len(self._classes))
            }
            return jsonify(counters)
        
        @self.app.route('/counters_images')
        def set_counters_images():
            counters_file = os.path.join(
                self._ROOT, "static", "counters", "counters.json"
            )
            with open(counters_file, 'r') as json_file:
                counters_imgs = json.load(json_file)
            return jsonify(counters_imgs)
