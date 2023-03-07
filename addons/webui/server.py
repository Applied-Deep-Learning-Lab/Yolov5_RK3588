from .media import MediaBlackhole, MediaRelay, InferenceTrack
from .utils import request_inference
from addons import storages as strgs
import asyncio
import json
import logging
import os
import uuid
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from multidict import MultiDict


class webUI():
    def __init__(self, raw_img_strg: strgs.ImageStorage, inf_img_strg: strgs.ImageStorage, dets_strg: strgs.DetectionsStorage):
        self._raw_img_strg = raw_img_strg
        self._inf_img_strg = inf_img_strg
        self._dets_strg = dets_strg
        self._ROOT = os.path.dirname(__file__)
        self._logger = logging.getLogger("pc")
        self._pcs = set()
        self._relay = MediaRelay()

    async def _index(self, request):
        """Response with main page HTML file on request"""
        content = open(os.path.join(self._ROOT, "index/index.html"), "r").read().replace('|Hostname|', os.uname()[1])
        return web.Response(content_type="text/html", text=content)

    async def _javascript(self, request):
        """Response with main page JavaScript client on request"""
        content = open(os.path.join(self._ROOT, "index/client.js"), "r").read()
        return web.Response(content_type="application/javascript", text=content)

    async def _style(self, request):
        """Response with main page CSS file on request"""
        content = open(os.path.join(self._ROOT, "index/style.css"), "r").read()
        return web.Response(content_type="text/css", text=content)

    # async def _settings_main(self, request):
    #     """Response with settings page HTML file on request"""
    #     if request.content_type == 'application/json':
    #         json_file = open(os.path.join(self._ROOT, "settings/settings.json"), 'r').read()
    #         return web.json_response(data=json_file)
    #     else:
    #         content = open(os.path.join(self._ROOT, "settings/index.html"), "r").read().replace('|Hostname|', os.uname()[1])
    #         return web.Response(content_type="text/html", text=content)

    # async def _settings_javascript(self, request):
    #     """Response with settings page JavaScript client on request"""
    #     content = open(os.path.join(self._ROOT, "settings/client.js"), "r").read()
    #     return web.Response(content_type="application/javascript", text=content)

    # async def _settings_style(self, request):
    #     """Response with settings page CSS file on request"""
    #     content = open(os.path.join(self._ROOT, "settings/style.css"), "r").read()
    #     return web.Response(content_type="text/css", text=content)

    # async def _update_settings(self, request):
    #     """Load and update settings to inference"""
    #     settings = await request.json()
    #     settings = sttgs.load_settings(settings=settings)
    #     inf.load_settings(settings['camera'])
    #     return web.Response(content_type="text", text="OK")

    # async def _update_model(self, request):
    #     """Retrieve model from request and loads it to inference"""
    #     model_form = await request.post()
    #     content = model_form["file"].file.read()
    #     inf.load_model(content[:])
    #     return web.Response(content_type="text", text="OK")

    # async def _send_model(self, request):
    #     """Send current running model"""
    #     model = os.path.join(self._ROOT, "yolov5m_leaky_352x352.rknn")
    #     headers = {'Content-Disposition': 'attachment; filename="yolov5m_leaky_352x352.rknn"'}
    #     return web.FileResponse(path=model, headers=headers)

    async def _send_inference(self, request):
        """
        Return path of inference.zip 
        containing number of inferenced images
        grabbed by settings in labelme format
        """
        path = await request_inference(
            dets_strg = self._dets_strg,
            raw_img_strg = self._raw_img_strg
        )
        if path is not None:
            return web.FileResponse(path=path, headers=MultiDict({'Content-Disposition': 'Attachment'}))
        return web.Response(content_type="text", text="ERR")

    async def _offer(self, request):
        """Initialize sdp session"""
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
        await pc.setLocalDescription(answer)

        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
            ),
        )

    async def _on_shutdown(self, app):
        # close peer connections
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
        # app.router.add_get("/settings", self._settings_main)
        # app.router.add_get("/settings/", self._settings_main)
        # app.router.add_get("/settings/client.js", self._settings_javascript)
        # app.router.add_get("/settings/styles.css", self._settings_style)
        # app.router.add_post("/settings", self._update_settings)
        # Model updating
        # app.router.add_post("/model", self._update_model)
        # Getting images and json for lableme
        app.router.add_get("/request_inference", self._send_inference)
        web.run_app(
            app, access_log=None, host='0.0.0.0', port=8080, ssl_context=ssl_context
        )