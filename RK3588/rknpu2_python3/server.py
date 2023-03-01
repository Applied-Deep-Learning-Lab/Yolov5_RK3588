import asyncio
import json
import logging
import os
import uuid
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from multidict import MultiDict
from media import MediaBlackhole, MediaRelay, InferenceTrack
from main_server import OrangePi
import settings.settings as sttgs


ROOT = os.path.dirname(__file__)

logger = logging.getLogger("pc")
pcs = set()
relay = MediaRelay()
inf = OrangePi() # Initializing and
inf.start()       # starting inference processes


async def index(request):
    """Response with main page HTML file on request"""
    content = open(os.path.join(ROOT, "index/index.html"), "r").read().replace('|Hostname|', os.uname()[1])
    return web.Response(content_type="text/html", text=content)


async def javascript(request):
    """Response with main page JavaScript client on request"""
    content = open(os.path.join(ROOT, "index/client.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def style(request):
    """Response with main page CSS file on request"""
    content = open(os.path.join(ROOT, "index/style.css"), "r").read()
    return web.Response(content_type="text/css", text=content)


async def settings_main(request):
    """Response with settings page HTML file on request"""
    if request.content_type == 'application/json':
        json_file = open(os.path.join(ROOT, "settings/settings.json"), 'r').read()
        return web.json_response(data=json_file)
    else:
        content = open(os.path.join(ROOT, "settings/index.html"), "r").read().replace('|Hostname|', os.uname()[1])
        return web.Response(content_type="text/html", text=content)
    

async def settings_javascript(request):
    """Response with settings page JavaScript client on request"""
    content = open(os.path.join(ROOT, "settings/client.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def settings_style(request):
    """Response with settings page CSS file on request"""
    content = open(os.path.join(ROOT, "settings/style.css"), "r").read()
    return web.Response(content_type="text/css", text=content)


async def update_settings(request):
    """Load and update settings to inference"""
    settings = await request.json()
    settings = sttgs.load_settings(settings=settings)
    inf.load_settings(settings['camera'])
    return web.Response(content_type="text", text="OK")


async def update_model(request):
    """Retrieve model from request and loads it to inference"""
    model_form = await request.post()
    content = model_form["file"].file.read()
    inf.load_model(content[:])
    return web.Response(content_type="text", text="OK")


async def send_model(request):
    """Send current running model"""
    model = os.path.join(ROOT, "yolov5m_leaky_352x352.rknn")
    headers = {'Content-Disposition': 'attachment; filename="yolov5m_leaky_352x352.rknn"'}
    return web.FileResponse(path=model, headers=headers)


async def send_inference(request):
    """
    Return path of inference.zip 
    containing number of inferenced images
    grabbed by settings in labelme format
    """
    path = await inf.request_inference()
    if path is not None:
        return web.FileResponse(path=path, headers=MultiDict({'Content-Disposition': 'Attachment'}))
    return web.Response(content_type="text", text="ERR")


async def offer(request):
    """Initialize sdp session"""
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    pc = RTCPeerConnection()
    pc_id = "PeerConnection(%s)" % uuid.uuid4()
    pcs.add(pc)

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
            pcs.discard(pc)
            return
        elif pc.connectionState == "closed":
            await pc.close()
            pcs.discard(pc)
            return

    @pc.on("track")
    def on_track(track):
        log_info("Track %s received", track.kind)

        nonlocal videoTrackProducer
        videoTrackProducer = InferenceTrack(inf)
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


async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()


def main():
    logging.basicConfig(level=logging.ERROR)
    ssl_context = None
    # Creating Application instance
    app = web.Application()
    app._client_max_size = 160000000
    app.on_shutdown.append(on_shutdown)
    # Routing adresses for each function
    app.router.add_get("/", index)
    app.router.add_get("/styles.css", style)
    app.router.add_get("/client.js", javascript)
    app.router.add_post("/offer", offer)

    app.router.add_get("/settings", settings_main)
    app.router.add_get("/settings/", settings_main)
    app.router.add_get("/settings/client.js", settings_javascript)
    app.router.add_get("/settings/styles.css", settings_style)
    app.router.add_post("/settings", update_settings)

    app.router.add_post("/model", update_model)
    # app.router.add_post("/model", send_model)
    app.router.add_get("/request_inference", send_inference)
    web.run_app(
        app, access_log=None, host='0.0.0.0', port=8080, ssl_context=ssl_context
    )

if __name__ == "__main__":
    main()