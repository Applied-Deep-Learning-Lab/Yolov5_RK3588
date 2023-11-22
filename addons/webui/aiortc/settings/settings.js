// Get settings elements

/// Base
let debug_state = document.getElementById("debug_state");
let verbose_state = document.getElementById("verbose_state");
let async_mode = document.getElementById("async_mode_state");
let buf_size = document.getElementById("buf_size");

/// Camera
let show_state = document.getElementById("show_state");
let source = document.getElementById("source");
let width = document.getElementById("width");
let height = document.getElementById("height");
let pixel_format = document.getElementById("pixel_format");
let camera_fps = document.getElementById("camera_framerate");

/// Neural Network
let sigmoid = document.getElementById("sigmoid");
let net_size = document.getElementById("net_size");
let obj_thresh = document.getElementById("obj_thresh");
let nms_thresh = document.getElementById("nms_thresh");
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

  /// Base
  debug_state.checked = settings_data.base.debug;
  verbose_state.checked = settings_data.base.verbose;
  async_mode.checked = settings_data.base.inference.async_mode;
  buf_size.value = settings_data.base.inference.buf_size;
  send_data_amount.value = settings_data.base.webui.send_data_amount;

  /// Camera
  show_state.checked = settings_data.base.camera.show;
  source.value = settings_data.base.camera.source;
  width.value = settings_data.base.camera.width;
  height.value = settings_data.base.camera.height;
  pixel_format.value = settings_data.base.camera.pixel_format;
  camera_fps.value = settings_data.base.camera.fps;

  /// Neural Network
  sigmoid.checked = settings_data.neural_network.sigmoid;
  net_size.value = settings_data.neural_network.net_size;
  obj_thresh.value = settings_data.neural_network.obj_thresh;
  nms_thresh.value = settings_data.neural_network.nms_thresh;

  /// Addons
  //// Storages
  storages_state.checked = settings_data.base.storages.state;
  stored_data_amount.value = settings_data.base.storages.stored_data_amount;
  dets_amount.value = settings_data.base.storages.dets_amount;
  frames_delay.value = settings_data.base.storages.frames_delay;

  //// BYTEtrack
  bytetrack_state.checked = settings_data.base.bytetrack.state;
  bytetrack_fps.value = settings_data.base.bytetrack.fps;

  //// Telegram notifier
  telegram_notifier.checked = settings_data.base.telegram_notifier.state;
  time_period.value = settings_data.base.telegram_notifier.time_period;
  bot_token.value = settings_data.base.telegram_notifier.token;
  chat_id.value = settings_data.base.telegram_notifier.chat_id;
}

async function SendSettingsValues() {
  // Get settings (json file data) for formatting
  let response = await fetch("/settings_values", {
    method: "GET",
  });
  let settings_data = await response.json();
  // Set settings values from page
  /// Base
  settings_data.base.debug = debug_state.checked;
  settings_data.base.verbose = verbose_state.checked;
  settings_data.base.inference.async_mode = async_mode.checked;
  settings_data.base.inference.buf_size = Number(buf_size.value);
  settings_data.base.webui.send_data_amount = Number(send_data_amount.value);

  /// Camera
  settings_data.base.camera.show = show_state.checked;
  settings_data.base.camera.source = Number(source.value);
  settings_data.base.camera.width = Number(width.value);
  settings_data.base.camera.height = Number(height.value);
  settings_data.base.camera.pixel_format = pixel_format.value;
  settings_data.base.camera.fps = Number(camera_fps.value);

  /// Neural Network
  settings_data.neural_network.sigmoid = sigmoid.checked;
  settings_data.neural_network.net_size = Number(net_size.value);
  settings_data.neural_network.obj_thresh = Number(obj_thresh.value);
  settings_data.neural_network.nms_thresh = Number(nms_thresh.value);

  /// Addons
  //// Storages
  settings_data.base.storages.state = storages_state.checked;
  settings_data.base.storages.stored_data_amount = Number(
    stored_data_amount.value
  );
  settings_data.base.storages.dets_amount = Number(dets_amount.value);
  settings_data.base.storages.frames_delay = Number(frames_delay.value);

  //// BYTEtrack
  settings_data.base.bytetrack.state = bytetrack_state.checked;
  settings_data.base.bytetrack.fps = Number(bytetrack_fps.value);

  //// Telegram notifier
  settings_data.base.telegram_notifier.state = telegram_notifier.checked;
  settings_data.base.telegram_notifier.time_period = Number(time_period.value);
  settings_data.base.telegram_notifier.token = bot_token.value;
  settings_data.base.telegram_notifier.chat_id = chat_id.value;

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
  let new_model_file = document.getElementById("new_model_file").files[0];
  if (typeof new_model_file === "undefined") {
    showModal("Model", "Please, choose file for uploading.", 2500, true);
  } else {
    const formData = new FormData();
    formData.append("file", new_model_file);
    fetch("/model", {
      method: "POST",
      body: formData,
    });
    showModal("Model", "Uploading...", 5000);
  }
}

function updateLocalModel() {
  let local_model = document.getElementById("select_local_model").value;
  if (local_model === "Select model from local...") {
    showModal("Model", "Please, choose model for changing.", 2500, true);
  } else {
    const formData = new FormData();
    formData.append("text", local_model);
    fetch("/model", {
      method: "POST",
      body: formData,
    });
    showModal("Model", "Changing...", 1000);
  }
}

function showModal(LabelText, ContentText, LoadTime, warning = false) {
  let modal = document.getElementById("SettingsModal");
  let label = document.getElementById("SettingsModalLabel");
  let content = document.getElementById("SettingsModalContent");
  let footer = document.getElementById("SettingsModalFooter");
  label.innerText = LabelText;
  content.innerText = ContentText;
  footer.className += " visually-hidden";
  modal.style.display = "block";
  if (warning) {
    setTimeout(function () {
      modal.style.display = "";
    }, LoadTime);
  } else {
    setTimeout(function () {
      footer.className = footer.className.split(" ")[0];
      content.innerText = "Successfuly!!!";
    }, LoadTime);
  }
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

function SettingsUpdateModal() {
  let modal = document.getElementById("SettingsModal");
  let label = document.getElementById("SettingsModalLabel");
  let content = document.getElementById("SettingsModalContent");
  let footer = document.getElementById("SettingsModalFooter");
  label.innerText = "Settings";
  content.innerText = "Successfuly updated!!!";
  footer.className = footer.className.split(" ")[0];
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
