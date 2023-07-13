import logging
import os

from flask import Flask, Response, jsonify, render_template, request

from addons.webui_flask.utils import video
from addons.storages import ImageStorage

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
    def __init__(self, inf_img_strg: ImageStorage):
        self._inf_img_strg = inf_img_strg
        self.app = Flask(__name__)

        @self.app.route('/')
        def home_page() -> str:
            return render_template("home.html")


        @self.app.route('/settings/')
        def settings_page() -> str:
            return render_template('settings.html')


        @self.app.route('/settings/', methods=["POST"])
        def settings_page_update() -> Response:
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
            return jsonify({"message": "Settings updated."})

        @self.app.route('/video_feed')
        def video_feed():
            return Response(
                response=video.gen_frame(
                    self._inf_img_strg.get_last_data()
                ),
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )