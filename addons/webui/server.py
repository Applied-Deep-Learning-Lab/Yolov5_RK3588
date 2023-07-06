import asyncio
import json
import logging
import os
import sys

import cv2
import numpy as np
import psutil
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from multidict import MultiDict

import addons.storages as strgs
from base.camera import Cam
from config import RK3588_CFG, YOLOV5_CFG

from .media import InferenceTrack, MediaBlackhole, MediaRelay
from .utils import request_inference

MODELS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "/models/"
)

# Create the server's logger
server_logger = logging.getLogger("server")
server_logger.setLevel(logging.DEBUG)
# Create handler that output all info to the console
server_console_handler = logging.StreamHandler()
server_console_handler.setLevel(logging.DEBUG)
# Create handler that output errors, warnings to the file
server_file_handler = logging.FileHandler(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "log/server.log"
    )
)
server_file_handler.setLevel(logging.ERROR)
# Create formatter for handlers
server_formatter = logging.Formatter(
    fmt="%(levelname)s - %(asctime)s: %(message)s.",
    datefmt="%d-%m-%Y %H:%M:%S"
)
server_console_handler.setFormatter(server_formatter)
server_file_handler.setFormatter(server_formatter)
# Add handlers to the logger
server_logger.addHandler(server_console_handler)
server_logger.addHandler(server_file_handler)


class WebUI():
    """Class for Web User Interface

    Args
    ---------------------------------------------------------------------------
    raw_img_strg: storages.ImageStorage
        Object of ImageStorage that stored raw frames
    inf_img_strg: storages.ImageStorage
        Object of ImageStorage that stored inferenced frames
    dets_strg: storages.DetectionsStorage
        Object of DetectionsStorage that stored numpy array with detections
    camera: Cam
        Object of Cam for release camera
    ---------------------------------------------------------------------------

    Attributes
    ---------------------------------------------------------------------------
    _raw_img_strg: storages.ImageStorage
        Object of ImageStorage that stored raw frames
    _inf_img_strg: storages.ImageStorage
        Object of ImageStorage that stored inferenced frames
    _dets_strg: storages.DetectionsStorage
        Object of DetectionsStorage that stored numpy array with detections
    _ROOT: str
        Path to addon's root directory
    _pcs: set
    _relay: MediaRelay
    ---------------------------------------------------------------------------

    Methods
    ---------------------------------------------------------------------------
    _index(request): web.Response
        Response with main page HTML file on request
    _javascript(request): web.Response
        Response with main page JavaScript client on request
    _update_model(request): web.Response
        Retrieve model from request and loads it to inference
    _show_models(request): web.Response
        Send all uploaded models to show
    _update_settings(request): web.Response
        Retrieve settings from request and loads it to inference
    _send_inference: web.Response | web.FileResponse
        Return path of inference.zip 
        containing number of inferenced images
        grabbed by settings in labelme format
    _offer(request): web.Response
        Initialize sdp session
    _on_shutdown(request): web.Response
        Close peer connections
    start(): None
        Starts Web User Interface
    ---------------------------------------------------------------------------
    """

    def __init__(
            self,
            raw_img_strg: strgs.ImageStorage,
            inf_img_strg: strgs.ImageStorage,
            dets_strg: strgs.DetectionsStorage,
            counters_strg: strgs.Storage,
            camera: Cam
    ):
        self._raw_img_strg = raw_img_strg
        self._inf_img_strg = inf_img_strg
        self._dets_strg = dets_strg
        self._counters_strg = counters_strg
        self._cam = camera
        self._classes = YOLOV5_CFG["inference"]["classes"]
        self._ROOT = os.path.dirname(__file__)
        self._pcs = set()
        self._relay = MediaRelay()
        self._blank_frame = np.zeros(
            shape=(
                RK3588_CFG["camera"]["height"],
                RK3588_CFG["camera"]["width"],
                3
            ),
            dtype=np.uint8
        )
        cv2.putText(
            img=self._blank_frame,
            text="BAD SOURCE",
            org=(
                int(self._blank_frame.shape[1]/2 - 95),
                int(self._blank_frame.shape[0]/2 - 15)
            ),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=0.9,
            color=(123, 123, 0),
            thickness=3,
            lineType=cv2.LINE_AA
        )

    async def _home(self, request):
        content = open(
            file=os.path.join(self._ROOT, "home/home.html"),
            mode='r'
        ).read().replace('|Hostname|', os.uname()[1])
        return web.Response(content_type="text/html", text=content)

    async def _javascript(self, request):
        content = open(os.path.join(self._ROOT, "home/client.js"), "r").read()
        return web.Response(content_type="application/javascript", text=content)

    async def _settings(self, request):
        content = open(
            file=os.path.join(self._ROOT, "settings/settings.html"),
            mode='r'
        ).read().replace('|Hostname|', os.uname()[1])
        return web.Response(content_type="text/html", text=content)

    async def _settings_javascript(self, request):
        content = open(
            os.path.join(self._ROOT, "settings/settings.js"), 'r'
        ).read()
        return web.Response(content_type="application/javascript", text=content)

    async def _send_settings(self, request):
        return web.json_response(data=RK3588_CFG)

    async def _get_settings(self, request):
        model_form = await request.post()
        settings_values = json.loads(model_form["text"])
        RK3588_CFG[:] = settings_values[:]
        RK3588_CFG.update()
        server_logger.info("Settings loaded")
        return web.Response(content_type="text", text="OK")

    async def _send_inference(self, request):
        path = await request_inference(
            dets_strg=self._dets_strg,
            raw_img_strg=self._raw_img_strg
        )
        if path is not None:
            return web.FileResponse(
                path=path,
                headers=MultiDict({'Content-Disposition': 'Attachment'})
            )
        return web.Response(content_type="text", text="ERR")

    async def _show_models(self, request):
        local_models = os.listdir(MODELS)
        models = [
            model for model in local_models if ".rknn" in model
        ]
        return web.Response(text=json.dumps(models))

    async def _update_model(self, request):
        def _load_new_model(new_model: bytes, new_model_name: str):
            """Create file for new model and rewrite path"""
            if "640" in new_model_name:
                YOLOV5_CFG["net_size"] = 640
            elif "352" in new_model_name:
                YOLOV5_CFG["net_size"] = 352
            YOLOV5_CFG["new_model"] = new_model_name
            YOLOV5_CFG.update()
            with open(os.path.join(MODELS, new_model_name), "wb") as f:
                f.write(new_model)
            server_logger.info("Model loaded")

        def _load_local_model(local_model):
            """Rewrite path to running model"""
            YOLOV5_CFG["new_model"] = local_model
            YOLOV5_CFG.update()
            server_logger.info("Model changed")

        model_form = await request.post()
        if "file" in model_form.keys():
            _load_new_model(
                new_model=model_form["file"].file.read(),
                new_model_name=model_form["file"].filename
            )
        else:
            _load_local_model(
                local_model=model_form["text"]
            )
        return web.Response(content_type="text", text="OK")

    async def _set_counters_images(self, request):
        with open(self._ROOT + "/counters/counters.json", 'r') as json_file:
            counters_imgs = json.load(json_file)
        return web.json_response(data=counters_imgs)

    async def _set_counters(self, request):
        counters = {
            self._classes[i]: int(self._counters_strg.get_data_by_index(i)) # type: ignore
            for i in range(len(self._classes))
        }
        counters = json.dumps(counters)
        counters = json.loads(counters)
        return web.json_response(data=counters)

    async def _set_temperature(self, request):
        temperature = psutil.sensors_temperatures()["center_thermal"][0][1]
        return web.Response(text=str(temperature))

    async def _restart_program(self, request):
        server_logger.info("Restartung program.")
        self._cam.release()
        args = [sys.executable] + sys.argv
        os.execv(sys.executable, args)

    async def _reboot_device(self, request):
        server_logger.info("Rebooting device.")
        os.system("reboot")
        return web.Response(content_type="text", text="OK")

    async def _offer(self, request):
        params = await request.json()
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
        pc = RTCPeerConnection()
        self._pcs.add(pc)

        videoTrackProducer = None

        def log_info(msg, *args):
            pass

        log_info("Created for %s", request.remote)
        server_logger.info(f"Created for {request.remote}")

        recorder = MediaBlackhole()  # MediaRecorder("/root/sample.mp4")

        @pc.on("datachannel")
        def on_datachannel(channel):
            @channel.on("message")
            def on_message(message):
                log_info('on_message ' + message)
                server_logger.info(f'on_message {message}')
                if isinstance(message, str):
                    if message.startswith("ping"):
                        channel.send("pong" + message[4:])

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            log_info("Connection state is %s", pc.connectionState)
            server_logger.info(f"Connection state is {pc.connectionState}")
            if pc.connectionState == "failed":
                await pc.close()
                self._pcs.discard(pc)
                return
            elif pc.connectionState == "closed":
                await pc.close()
                self._pcs.discard(pc)
                return

        @pc.on("track")
        def on_track(track):
            log_info("Track %s received", track.kind)
            server_logger.info(f"Track {track.kind} received")

            nonlocal videoTrackProducer
            videoTrackProducer = InferenceTrack(
                self._inf_img_strg,
                self._blank_frame
            )
            pc.addTrack(videoTrackProducer)
            videoTrackProducer.onClientShowedFrameInfo(0)

            @track.on("ended")
            async def on_ended():
                log_info("Track %s ended", track.kind)
                server_logger.info(f"Track {track.kind} ended")
                await recorder.stop()

        # handle offer
        await pc.setRemoteDescription(offer)
        await recorder.start()

        # send answer
        answer = await pc.createAnswer()
        if answer is not None:
            await pc.setLocalDescription(answer)

        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {
                    "sdp": pc.localDescription.sdp,
                    "type": pc.localDescription.type
                }
            ),
        )

    async def _on_shutdown(self, app):
        coros = [pc.close() for pc in self._pcs]
        await asyncio.gather(*coros)
        self._pcs.clear()

    def start(self):
        ssl_context = None
        # Creating Application instance
        app = web.Application()
        app._client_max_size = 160000000
        app.on_shutdown.append(self._on_shutdown)
        # Routing adresses for each function
        # home page
        app.router.add_get("/", self._home)
        app.router.add_get("/client.js", self._javascript)
        # settings page
        app.router.add_get("/settings", self._settings)
        app.router.add_get("/settings.js", self._settings_javascript)
        app.router.add_get("/settings_values", self._send_settings)
        app.router.add_post("/settings_values", self._get_settings)
        # Getting images and json for lableme
        app.router.add_get("/request_inference", self._send_inference)
        # Showing local models
        app.router.add_get("/show_models", self._show_models)
        # Model updating
        app.router.add_post("/model", self._update_model)
        # get couners images and data
        app.router.add_get("/counters_images", self._set_counters_images)
        app.router.add_get("/counters_data", self._set_counters)
        # get cpu temperature
        app.router.add_get("/cpu_temperature", self._set_temperature)
        # Restart program
        app.router.add_post("/restart", self._restart_program)
        # Reboot device
        app.router.add_post("/reboot", self._reboot_device)
        # sdp session
        app.router.add_post("/offer", self._offer)
        server_logger.info("Starting WebUI server")
        web.run_app(
            app,
            access_log=None,
            host='0.0.0.0',
            port=8080,
            ssl_context=ssl_context
        )
