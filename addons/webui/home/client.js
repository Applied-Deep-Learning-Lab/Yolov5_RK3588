// get DOM elements
var dataChannelLog = null,
  iceConnectionLog = null,
  iceGatheringLog = null,
  signalingLog = null;

const videoControl = null;
// peer connection
var pc = null;

// data channel
var dc = null,
  dcPingInterval = null,
  dcReportFrameInterval = null;
const fps = 25;
var settings = null;

function createPeerConnection() {
  var config = {
    sdpSemantics: "unified-plan",
  };

  if (document.getElementById("use-stun").checked) {
    config.iceServers = [{ urls: ["stun:stun.l.google.com:19302"] }];
  }

  pc = new RTCPeerConnection(config);

  // register some listeners to help debugging
  pc.addEventListener(
    "icegatheringstatechange",
    function () {
      iceGatheringLog.textContent += " -> " + pc.iceGatheringState;
    },
    false
  );
  iceGatheringLog.textContent = pc.iceGatheringState;

  pc.addEventListener(
    "iceconnectionstatechange",
    function () {
      iceConnectionLog.textContent += " -> " + pc.iceConnectionState;
    },
    false
  );
  iceConnectionLog.textContent = pc.iceConnectionState;

  pc.addEventListener(
    "signalingstatechange",
    function () {
      signalingLog.textContent += " -> " + pc.signalingState;
    },
    false
  );
  signalingLog.textContent = pc.signalingState;

  // connect audio / video
  pc.addEventListener("track", function (evt) {
    if (evt.track.kind == "video")
      document.getElementById("video").srcObject = evt.streams[0];
    else document.getElementById("audio").srcObject = evt.streams[0];
  });

  return pc;
}

function negotiate() {
  const offerOptions = {
    offerToReceiveAudio: 1,
    offerToReceiveVideo: 1,
  };

  return pc
    .createOffer(offerOptions)
    .then(function (offer) {
      return pc.setLocalDescription(offer);
    })
    .then(function () {
      // wait for ICE gathering to complete
      return new Promise(function (resolve) {
        if (pc.iceGatheringState === "complete") {
          resolve();
        } else {
          function checkState() {
            if (pc.iceGatheringState === "complete") {
              pc.removeEventListener("icegatheringstatechange", checkState);
              resolve();
            }
          }
          pc.addEventListener("icegatheringstatechange", checkState);
        }
      });
    })
    .then(function () {
      var offer = pc.localDescription;
      var codec;

      codec = document.getElementById("audio-codec").value;
      if (codec !== "default") {
        offer.sdp = sdpFilterCodec("audio", codec, offer.sdp);
      }

      codec = document.getElementById("video-codec").value;
      if (codec !== "default") {
        offer.sdp = sdpFilterCodec("video", codec, offer.sdp);
      }

      let video_source = "file";
      let elem = document.getElementById("video-source");
      if (elem != null) video_source = elem.value;

      document.getElementById("offer-sdp").textContent = offer.sdp;
      return fetch("/offer", {
        body: JSON.stringify({
          sdp: offer.sdp,
          type: offer.type,
          video_source: video_source,
          video_transform: document.getElementById("video-transform").value,
        }),
        headers: {
          "Content-Type": "application/json",
        },
        method: "POST",
      });
    })
    .then(function (response) {
      return response.json();
    })
    .then(function (answer) {
      document.getElementById("answer-sdp").textContent = answer.sdp;
      return pc.setRemoteDescription(answer);
    })
    .catch(function (e) {
      alert(e);
    });
}

// This event if not fired every frame, so with % 8 we can often reach the end
// without notifying server
function onFramePlayed() {}

function onSeekingByVideo() {}

function start() {
  (dataChannelLog = document.getElementById("data-channel")),
    (iceConnectionLog = document.getElementById("ice-connection-state"));
  iceGatheringLog = document.getElementById("ice-gathering-state");
  signalingLog = document.getElementById("signaling-state");
  const videoControl = document.querySelector("video");
  videoControl.controls = true;
  pc = createPeerConnection();
  var time_start = null;

  function current_stamp() {
    if (time_start === null) {
      time_start = new Date().getTime();
      return 0;
    } else {
      return new Date().getTime() - time_start;
    }
  }

  if (document.getElementById("use-datachannel").checked) {
    // Actually we can't play video normally without data channel anymore
    var parameters = JSON.parse(
      document.getElementById("datachannel-parameters").value
    );

    dc = pc.createDataChannel("chat", parameters);
    dc.onclose = function () {
      clearInterval(dcPingInterval);
      dataChannelLog.textContent += "- close\n";
    };
    dc.onopen = function () {
      dataChannelLog.textContent += "- open\n";
      dcPingInterval = setInterval(function () {
        var message = "ping " + current_stamp();
        dataChannelLog.textContent += "> " + message + "\n";
        dc.send(message);
      }, 5000);
    };

    dc.onmessage = function (evt) {
      dataChannelLog.textContent += "< " + evt.data + "\n";
      if (evt.data.substring(0, 4) === "pong") {
        var elapsed_ms = current_stamp() - parseInt(evt.data.substring(5), 10);
        dataChannelLog.textContent += " RTT " + elapsed_ms + " ms\n";
      }
    };
  }

  var constraints = {
    audio: document.getElementById("use-audio").checked,
    video: false,
  };

  let silence = () => {
    let ctx = new AudioContext(),
      oscillator = ctx.createOscillator();
    let dst = oscillator.connect(ctx.createMediaStreamDestination());
    oscillator.start();
    return Object.assign(dst.stream.getAudioTracks()[0], { enabled: false });
  };

  let black = ({ width = 1, height = 1 } = {}) => {
    let canvas = Object.assign(document.createElement("canvas"), {
      width,
      height,
    });
    canvas.getContext("2d").fillRect(0, 0, width, height);
    let stream = canvas.captureStream();
    return Object.assign(stream.getVideoTracks()[0], { enabled: false });
  };

  if (document.getElementById("use-video").checked) {
    var resolution = document.getElementById("video-resolution").value;
    if (resolution) {
      resolution = resolution.split("x");
      constraints.video = {
        width: parseInt(resolution[0], 0),
        height: parseInt(resolution[1], 0),
      };
    } else {
      constraints.video = true;
    }
  }

  if (constraints.audio || constraints.video) {
    let streams = [];
    if (constraints.audio) streams.push(silence());
    if (constraints.video) streams.push(black());
    stream = new MediaStream(streams);
    stream.getTracks().forEach(function (track) {
      pc.addTrack(track, stream);
    });
    negotiate();

    let sentFrameNum = 0;

    dcReportFrameInterval = setInterval(function () {
      let frameNum = videoControl.webkitDecodedFrameCount;
      signalingLog.textContent =
        frameNum +
        "  " +
        videoControl.webkitDroppedFrameCount +
        " " +
        videoControl.currentTime +
        " (" +
        videoControl.currentTime * fps +
        ")";
      frameNum = Math.round(videoControl.currentTime * fps);
      if (frameNum == sentFrameNum) return;
      sentFrameNum = frameNum;
    }, 300);
  }

  videoControl.addEventListener("timeupdate", onFramePlayed);
  videoControl.addEventListener("seeking", onSeekingByVideo);
}

function stop() {
  if (dc) {
    dc.close();
  }
  if (pc.getTransceivers) {
    pc.getTransceivers().forEach(function (transceiver) {
      if (transceiver.stop) {
        transceiver.stop();
      }
    });
  }

  // close local audio / video
  pc.getSenders().forEach(function (sender) {
    sender.track.stop();
  });

  // close peer connection
  setTimeout(function () {
    pc.close();
  }, 500);
}

function sdpFilterCodec(kind, codec, realSdp) {
  var allowed = [];
  var rtxRegex = new RegExp("a=fmtp:(\\d+) apt=(\\d+)\r$");
  var codecRegex = new RegExp("a=rtpmap:([0-9]+) " + escapeRegExp(codec));
  var videoRegex = new RegExp("(m=" + kind + " .*?)( ([0-9]+))*\\s*$");

  var lines = realSdp.split("\n");

  var isKind = false;
  for (var i = 0; i < lines.length; i++) {
    if (lines[i].startsWith("m=" + kind + " ")) {
      isKind = true;
    } else if (lines[i].startsWith("m=")) {
      isKind = false;
    }

    if (isKind) {
      var match = lines[i].match(codecRegex);
      if (match) {
        allowed.push(parseInt(match[1]));
      }

      match = lines[i].match(rtxRegex);
      if (match && allowed.includes(parseInt(match[2]))) {
        allowed.push(parseInt(match[1]));
      }
    }
  }

  var skipRegex = "a=(fmtp|rtcp-fb|rtpmap):([0-9]+)";
  var sdp = "";

  isKind = false;
  for (var i = 0; i < lines.length; i++) {
    if (lines[i].startsWith("m=" + kind + " ")) {
      isKind = true;
    } else if (lines[i].startsWith("m=")) {
      isKind = false;
    }

    if (isKind) {
      var skipMatch = lines[i].match(skipRegex);
      if (skipMatch && !allowed.includes(parseInt(skipMatch[2]))) {
        continue;
      } else if (lines[i].match(videoRegex)) {
        sdp += lines[i].replace(videoRegex, "$1 " + allowed.join(" ")) + "\n";
      } else {
        sdp += lines[i] + "\n";
      }
    } else {
      sdp += lines[i] + "\n";
    }
  }

  return sdp;
}

function requestInference() {
  fetch("/request_inference", {
    method: "GET",
  })
    .then((response) => response.blob())
    .then((data) => {
      const d = new Date();
      name = new String(d.getTime() + ".zip");
      download(data, name, "multipart/mixed");
    });
}

function download(response, fileName, contentType) {
  var a = document.createElement("a");
  var file = response;
  a.href = URL.createObjectURL(file);
  a.download = fileName;
  a.click();
}

function ResetModalShow() {
  let modal = document.getElementById("ResetModal");
  modal.style.display = "block";
}

function CloseResetModal() {
  let modal = document.getElementById("ResetModal");
  modal.style.display = "none";
}

function RestartProgram() {
  CloseResetModal();
  ShowResetWaitingModal();
  setTimeout(function () {
    fetch("/restart", {
      method: "POST",
      body: "",
    });
    setTimeout(function () {
      location.reload(true);
    }, 6500);
  }, 100);
}

function ShowResetWaitingModal() {
  let modal = document.getElementById("ResetWaitingModal");
  modal.style.display = "block";
}

function RebootDevice() {
  CloseResetModal();
  ShowRebootWaitingModal();
  rebooting = true;
  setTimeout(function () {
    fetch("/reboot", {
      method: "POST",
      body: "",
    }).then((response) => {
      dataChannelLog.textContent += "response: " + response + "\n";
    });
    setTimeout(function () {
      location.reload(true);
    }, 50000);
  }, 100);
}

function ShowRebootWaitingModal() {
  let modal = document.getElementById("RebootWaitingModal");
  modal.style.display = "block";
}
