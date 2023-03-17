import asyncio
import json
import logging
import os
import uuid
from pathlib import Path

from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from multidict import MultiDict

import addons.storages as strgs

from .media import InferenceTrack, MediaBlackhole, MediaRelay
from .utils import request_inference


# Getting config
ROOT = Path(__file__).parent.parent.parent.absolute()
CONFIG_FILE = str(ROOT) + "/config.json"


class WebUI():
    """Class for Web User Interface
    
    Args
    ---------------------------------------------------------------------------
    raw_img_strg : storages.ImageStorage
        Object of ImageStorage that stored raw frames
    inf_img_strg : storages.ImageStorage
        Object of ImageStorage that stored inferenced frames
    dets_strg : storages.DetectionsStorage
        Object of DetectionsStorage that stored numpy array with detections
    ---------------------------------------------------------------------------
    
    Attributes
    ---------------------------------------------------------------------------
    _raw_img_strg : storages.ImageStorage
        Object of ImageStorage that stored raw frames
    _inf_img_strg : storages.ImageStorage
        Object of ImageStorage that stored inferenced frames
    _dets_strg : storages.DetectionsStorage
        Object of DetectionsStorage that stored numpy array with detections
    _ROOT : str
        Path to addon's root directory
    _logger : Logger
    _pcs : set
    _relay : MediaRelay
    ---------------------------------------------------------------------------

    Methods
    ---------------------------------------------------------------------------
    _index(request) : web.Response
        Response with main page HTML file on request
    _javascript(request) : web.Response
        Response with main page JavaScript client on request
    _style(request) : web.Response
        Response with main page CSS file on request
    _update_model(request) : web.Response
        Retrieve model from request and loads it to inference
    _show_models(request) : web.Response
        Send all uploaded models to show
    _update_settings(request) : web.Response
        Retrieve settings from request and loads it to inference
    _send_inference : web.Response | web.FileResponse
        Return path of inference.zip 
        containing number of inferenced images
        grabbed by settings in labelme format
    _offer(request) : web.Response
        Initialize sdp session
    _on_shutdown(request) : web.Response
        Close peer connections
    start() : None
        Starts Web User Interface
    ---------------------------------------------------------------------------
    """
    def __init__(
            self,
            raw_img_strg: strgs.ImageStorage,
            inf_img_strg: strgs.ImageStorage,
            dets_strg: strgs.DetectionsStorage
        ):
        self._raw_img_strg = raw_img_strg
        self._inf_img_strg = inf_img_strg
        self._dets_strg = dets_strg
        self._ROOT = os.path.dirname(__file__)
        self._logger = logging.getLogger("pc")
        self._pcs = set()
        self._relay = MediaRelay()

    async def _index(self, request):
        content = open(
            file=os.path.join(self._ROOT, "index/index.html"),
            mode='r'
        ).read().replace('|Hostname|', os.uname()[1])
        return web.Response(content_type="text/html", text=content)

    async def _javascript(self, request):
        content = open(os.path.join(self._ROOT, "index/client.js"), "r").read()
        return web.Response(content_type="application/javascript", text=content)

    async def _style(self, request):
        content = open(os.path.join(self._ROOT, "index/style.css"), "r").read()
        return web.Response(content_type="text/css", text=content)

    async def _update_model(self, request):
        def _load_new_model(new_model: bytes, path_to_new_model: str):
            """Create file for new model and rewrite path"""
            with open(CONFIG_FILE, "r") as json_file:
                data = json.load(json_file)
            data["inference"]["path_to_new_model"] = path_to_new_model
            with open(CONFIG_FILE, "w") as json_file:
                json.dump(
                    obj = data,
                    fp = json_file,
                    indent = 4
                )
            with open(path_to_new_model, "wb") as f:
                f.write(new_model)
            print("Model loaded")

        def _load_local_model(local_model):
            """Rewrite path to running model"""
            with open(CONFIG_FILE, "r") as json_file:
                data = json.load(json_file)
            data["inference"]["path_to_new_model"] = local_model
            with open(CONFIG_FILE, "w") as json_file:
                json.dump(
                    obj = data,
                    fp = json_file,
                    indent = 4
                )
            print("Model changed")

        model_form = await request.post()
        if "file" in model_form.keys():
            _load_new_model(
                new_model = model_form["file"].file.read(),
                path_to_new_model = str(ROOT)+"/models/" + \
                    model_form["file"].filename
            )
        else:
            _load_local_model(
                local_model = model_form["text"]
            )
        return web.Response(content_type="text", text="OK")
    
    async def _show_models(self, request):
        models_dir = str(ROOT)+"/models/"
        local_models = os.listdir(models_dir)
        models = [
            models_dir + model for model in local_models if ".rknn" in model
        ]
        return web.Response(text=json.dumps(models))

    async def _update_settings(self, request):
        def _load_settings(settings):
            with open(CONFIG_FILE, "wb") as f:
                f.write(settings)
            print("Settings loaded")

        settings_form = await request.post()
        content = settings_form["file"].file.read()
        _load_settings(content[:])
        return web.Response(content_type="text", text="OK")

    async def _send_inference(self, request):
        path = await request_inference(
            dets_strg = self._dets_strg,
            raw_img_strg = self._raw_img_strg
        )
        if path is not None:
            return web.FileResponse(
                path=path,
                headers=MultiDict({'Content-Disposition': 'Attachment'})
            )
        return web.Response(content_type="text", text="ERR")

    async def _offer(self, request):
        params = await request.json()
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
        pc = RTCPeerConnection()
        pc_id = "PeerConnection(%s)" % uuid.uuid4()
        self._pcs.add(pc)

        videoTrackProducer = None

        def log_info(msg, *args):
            pass  # logger.info(pc_id + " " + msg, *args)

        log_info("Created for %s", request.remote)

        recorder = MediaBlackhole()  # MediaRecorder("/root/sample.mp4")

        @pc.on("datachannel")
        def on_datachannel(channel):
            @channel.on("message")
            def on_message(message):
                log_info('on_message ' + message)
                if isinstance(message, str):
                    if message.startswith("ping"):
                        channel.send("pong" + message[4:])

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            log_info("Connection state is %s", pc.connectionState)
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

            nonlocal videoTrackProducer
            videoTrackProducer = InferenceTrack(self._inf_img_strg)
            pc.addTrack(videoTrackProducer)
            videoTrackProducer.onClientShowedFrameInfo(0)

            @track.on("ended")
            async def on_ended():
                log_info("Track %s ended", track.kind)
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
        logging.basicConfig(level=logging.ERROR)
        ssl_context = None
        # Creating Application instance
        app = web.Application()
        app._client_max_size = 160000000
        app.on_shutdown.append(self._on_shutdown)
        # Routing adresses for each function
        app.router.add_get("/", self._index)
        app.router.add_get("/styles.css", self._style)
        app.router.add_get("/client.js", self._javascript)
        app.router.add_post("/offer", self._offer)
        # Camera/inference settings (set/update)
        app.router.add_post("/settings", self._update_settings)
        # Model updating
        app.router.add_post("/model", self._update_model)
        # Showing local models
        app.router.add_get("/show_models", self._show_models)
        # Getting images and json for lableme
        app.router.add_get("/request_inference", self._send_inference)
        web.run_app(
            app,
            access_log=None,
            host='0.0.0.0',
            port=8080,
            ssl_context=ssl_context
        )