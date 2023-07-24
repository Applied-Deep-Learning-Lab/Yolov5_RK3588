import json
import logging
import os
import sys
import time

import psutil
from flask import Flask, Response, jsonify, render_template, request, send_file
from werkzeug.datastructures import FileStorage

from addons.storages import DetectionsStorage, ImageStorage, Storage
from addons.webui_flask.utils import gen_frame, request_inference
from config import RK3588_CFG, Config

logger = logging.Logger("server")
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
            raw_img_strg: ImageStorage,
            dets_strg: DetectionsStorage,
            inf_img_strg: ImageStorage,
            counters_strg: Storage
    ):
        self._ROOT = os.path.dirname(__file__)
        self._MODELS = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "models"
        )
        self._raw_img_strg = raw_img_strg
        self._dets_strg = dets_strg
        self._inf_img_strg = inf_img_strg
        self._counters_strg = counters_strg
        self._net_cfg = net_cfg
        self._classes = net_cfg["classes"]
        self.app = Flask(__name__)
        # For fps
        # if RK3588_CFG["count_fps"]:
        #     self._last_frame_time = time.time()
        #     self._counter = 0
        #     self._calculated = False

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
            # if RK3588_CFG["count_fps"]:
            #     if last_index > cur_index:
            #         self._counter += 1
            #         cur_index = last_index
            #     if self._counter % RK3588_CFG["camera"]["fps"] == 0 and not self._calculated:
            #         calculated = True
            #         fps = RK3588_CFG["camera"]["fps"]/(time.time() - begin_time)
            #         begin_time = time.time()
            #         logger.debug(f"{fps:.2f}")
            #     if counter % RK3588_CFG["camera"]["fps"] != 0:
            #         calculated = False
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
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "resources", "counters", "counters.json"
            )
            with open(counters_file, 'r') as json_file:
                counters_imgs = json.load(json_file)
            return jsonify(counters_imgs)
        
        @self.app.route('/request_inference')
        def send_inference() -> Response:
            zip_file = request_inference(
                dets_strg=self._dets_strg,
                raw_img_strg=self._raw_img_strg
            )
            return send_file(zip_file, as_attachment=True)
        
        @self.app.route('/show_models')
        def show_models() -> Response:
            local_models = os.listdir(self._MODELS)
            models = [
                model for model in local_models if ".rknn" in model
            ]
            return jsonify(models)
        
        @self.app.route('/model', methods=["POST"])
        def update_model() -> Response:
            def _load_new_model(new_model: FileStorage):
                """Create file for new model and rewrite path"""
                model_name = new_model.filename
                new_model.save(
                    os.path.join(self._MODELS, model_name) # type: ignore
                )
                if "640" in model_name: # type: ignore
                    self._net_cfg["net_size"] = 640
                elif "352" in model_name: # type: ignore
                    self._net_cfg["net_size"] = 352
                self._net_cfg["new_model"] = model_name
                self._net_cfg.upload()
                logger.info("Model loaded")

            def _load_local_model(local_model):
                """Rewrite path to running model"""
                self._net_cfg["new_model"] = local_model
                self._net_cfg.upload()
                logger.info("Model changed")
            
            if 'file' in request.files:
                model = request.files["file"]
                _load_new_model(
                    new_model=model
                )
                return jsonify({"message": "Model loaded."})
            elif 'text' in request.form:
                _load_local_model(
                    local_model=request.form["text"]
                )
                return jsonify({"message": "Model changed."})
            else:
                return jsonify({"message": "No file or text data provided."})

        @self.app.route('/restart', methods=["POST"])
        def restart_program():
            args = [sys.executable] + sys.argv
            os.execv(sys.executable, args)

        @self.app.route('/reboot', methods=["POST"])
        def reboot_device():
            logger.info("Rebooting device")
            os.system("reboot")
            return jsonify({"message": "Rebooting device."})
