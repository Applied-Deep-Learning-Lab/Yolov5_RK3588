// Get settings elements
/// Base
//// Inference
let async_mode = document.getElementById("async_mode_state");
let net_size = document.getElementById("net_size");
let buf_size = document.getElementById("buf_size");
let obj_thresh = document.getElementById("obj_thresh");
let nms_thresh = document.getElementById("nms_thresh");
let inf_proc = document.getElementById("inf_proc");
let post_proc = document.getElementById("post_proc");
//// Camera
let show_state = document.getElementById("show_state");
let source = document.getElementById("source");
let width = document.getElementById("width");
let height = document.getElementById("height");
let pixel_format = document.getElementById("pixel_format");
let camera_fps = document.getElementById("camera_framerate");
//// Debug
let print_camera_release = document.getElementById("print_camera_release");
let showed_frame_id = document.getElementById("showed_frame_id");
let filled_frame_id = document.getElementById("filled_frame_id");
let send_data_amount = document.getElementById("send_data_amount");
/// Addons
////Storages
let storages_state = document.getElementById("storages_state");
let stored_data_amount = document.getElementById("stored_data_amount");
let dets_amount = document.getElementById("dets_amount");
let frames_delay = document.getElementById("frames_delay");
//// BYTEtrack
let bytetrack_state = document.getElementById("bytetrack_state");
let bytetrack_fps = document.getElementById("bytetrack_framerate");
//// Telegram notifier
let telegram_notifier = document.getElementById("telegram_notifier_state");
let time_period = document.getElementById("time_period");
let bot_token = document.getElementById("bot_token");
let chat_id = document.getElementById("chat_id");

// Set settings values from local json file
SetSettingsValues();

async function SetSettingsValues() {
  // Get settings (json file data)
  const response = await fetch("/settings_values", {
    method: "GET",
  });
  let settings_data = await response.json(response);
  /// Base functions
  //// Inference
  async_mode.checked = settings_data.inference.async_mode;
  net_size.value = settings_data.inference.net_size;
  buf_size.value = settings_data.inference.buf_size;
  obj_thresh.value = settings_data.inference.obj_thresh;
  nms_thresh.value = settings_data.inference.nms_thresh;
  inf_proc.value = settings_data.inference.inf_proc;
  post_proc.value = settings_data.inference.post_proc;
  //// Camera
  show_state.checked = settings_data.camera.show;
  source.value = settings_data.camera.source;
  width.value = settings_data.camera.width;
  height.value = settings_data.camera.height;
  pixel_format.value = settings_data.camera.pixel_format;
  camera_fps.value = settings_data.camera.fps;
  //// Debug
  print_camera_release.checked = settings_data.debug.print_camera_release;
  showed_frame_id.checked = settings_data.debug.showed_frame_id;
  filled_frame_id.checked = settings_data.debug.filled_frame_id;
  send_data_amount.value = settings_data.webui.send_data_amount;
  /// Addons functions
  //// Storages
  storages_state.checked = settings_data.storages.state;
  stored_data_amount.value = settings_data.storages.stored_data_amount;
  dets_amount.value = settings_data.storages.dets_amount;
  frames_delay.value = settings_data.storages.frames_delay;
  //// BYTEtrack
  bytetrack_state.checked = settings_data.bytetrack.state;
  bytetrack_fps.value = settings_data.bytetrack.fps;
  //// Telegram notifier
  telegram_notifier.checked = settings_data.telegram_notifier.state;
  time_period.value = settings_data.telegram_notifier.time_period;
  bot_token.value = settings_data.telegram_notifier.token;
  chat_id.value = settings_data.telegram_notifier.chat_id;
}

async function SendSettingsValues() {
  // Get settings (json file data) for formatting
  const response = await fetch("/settings_values", {
    method: "GET",
  });
  let settings_data = await response.json(response);
  settings_data = JSON.parse(settings_data);
  // Set settings values from page
  /// Base functions
  //// Inference
  settings_data.inference.async_mode = async_mode.checked;
  settings_data.inference.net_size = Number(net_size.value);
  settings_data.inference.buf_size = Number(buf_size.value);
  settings_data.inference.obj_thresh = Number(obj_thresh.value);
  settings_data.inference.nms_thresh = Number(nms_thresh.value);
  settings_data.inference.inf_proc = Number(inf_proc.value);
  settings_data.inference.post_proc = Number(post_proc.value);
  //// Camera
  settings_data.camera.show = show_state.checked;
  settings_data.camera.source = Number(source.value);
  settings_data.camera.width = Number(width.value);
  settings_data.camera.height = Number(height.value);
  settings_data.camera.pixel_format = pixel_format.value;
  settings_data.camera.fps = Number(camera_fps.value);
  //// Debug
  settings_data.debug.print_camera_release = print_camera_release.checked;
  settings_data.debug.showed_frame_id = showed_frame_id.checked;
  settings_data.debug.filled_frame_id = filled_frame_id.checked;
  settings_data.webui.send_data_amount = Number(send_data_amount.value);
  /// Addons functions
  //// Storages
  settings_data.storages.state = storages_state.checked;
  settings_data.storages.stored_data_amount = Number(stored_data_amount.value);
  settings_data.storages.dets_amount = Number(dets_amount.value);
  settings_data.storages.frames_delay = Number(frames_delay.value);
  //// BYTEtrack
  settings_data.bytetrack.state = bytetrack_state.checked;
  settings_data.bytetrack.fps = Number(bytetrack_fps.value);
  //// Telegram notifier
  settings_data.telegram_notifier.state = telegram_notifier.checked;
  settings_data.telegram_notifier.time_period = Number(time_period.value);
  settings_data.telegram_notifier.token = bot_token.value;
  settings_data.telegram_notifier.chat_id = chat_id.value;
  // Convert values to string for sending
  settings_data = JSON.stringify(settings_data);
  // Sending values to the device's config file
  let formData = new FormData();
  formData.append("text", settings_data);
  fetch("/settings_values", {
    method: "POST",
    body: formData,
  });
  SettingsUpdateModal();
}

async function showModels() {
  try {
    const response = await fetch("/show_models");
    let models = await response.json();
    // Creating select menu for local models
    let select = document.getElementById("select_local_model");
    select.innerHTML = "";
    // Creating options for choose local model
    for (let i = 0; i < models.length; i++) {
      let model = models[i];
      let el = document.createElement("option");
      el.textContent = model;
      el.value = model;
      select.add(el);
    }
  } catch (error) {
    console.error(error);
  }
}

function updateNewModel() {
  const formData = new FormData();
  formData.append("file", document.getElementById("new_model_file").files[0]);
  fetch("/model", {
    method: "POST",
    body: formData,
  });
  showModal("Model", "Uploading...", 5000);
}

function updateLocalModel() {
  const formData = new FormData();
  formData.append("text", document.getElementById("select_local_model").value);
  fetch("/model", {
    method: "POST",
    body: formData,
  });
  showModal("Model", "Changing...", 1000);
}

function RestartProgram() {
  CloseResetModal();
  CloseSettingsModal();
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

function RebootDevice() {
  CloseResetModal();
  CloseSettingsModal();
  ShowRebootWaitingModal();
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

function showModal(modalLabel, modalContent, loadTime) {
  let modal = document.getElementById("SettingsModal");
  let label = document.getElementById("SettingsModalLabel");
  label.innerText = modalLabel;
  let content = document.getElementById("SettingsModalContent");
  content.innerText = modalContent;
  modal.style.display = "block";
  setTimeout(function () {
    content.innerText = "Successfuly!!!";
  }, loadTime);
}

function SettingsUpdateModal() {
  let modal = document.getElementById("SettingsModal");
  modal.style.display = "block";
}

function CloseSettingsModal() {
  let modal = document.getElementById("SettingsModal");
  modal.style.display = "none";
}

function ResetModalShow() {
  let modal = document.getElementById("ResetModal");
  modal.style.display = "block";
}

function CloseResetModal() {
  let modal = document.getElementById("ResetModal");
  modal.style.display = "none";
}

function ShowResetWaitingModal() {
  let modal = document.getElementById("ResetWaitingModal");
  modal.style.display = "block";
}

function ShowRebootWaitingModal() {
  let modal = document.getElementById("RebootWaitingModal");
  modal.style.display = "block";
}