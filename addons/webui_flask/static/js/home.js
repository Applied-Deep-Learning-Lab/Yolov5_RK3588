function updateFrame() {
  try {
    setInterval(function () {
      fetch("/video_feed")
        .then((response) => response.blob())
        .then((blob) => {
          var img = document.getElementById("frame");
          img.src = URL.createObjectURL(blob);
        });
    }, 10);
  } catch (error) {
    console.log(error);
  }
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

async function CreateCounters() {
  // Getting counters (json file data)
  const response = await fetch("/counters_images", {
    method: "GET",
  });
  let counters_data = await response.json(response);
  let obj = 0;
  // Getting grid for fill it with objects
  let counters_grid = document.getElementById("CountersGrid");
  let counters_row;
  // Creating new row in grid
  for (let counter in counters_data) {
    if (obj % 8 === 0) {
      counters_row = document.createElement("div");
      counters_row.className = "row mb-3 mt-3";
    }
    // Creating space for insert object info
    let counters_col = document.createElement("div");
    counters_col.className = "col col-row-3";
    // Creating object label
    let object_name = document.createElement("label");
    object_name.innerText = counter;
    // Creating object image
    let div_object_img = document.createElement("div");
    let object_img = document.createElement("img");
    object_img.src = counters_data[counter].img_src;
    object_img.width = 80;
    object_img.height = 80;
    object_img.alt = counter;
    // Creating object counter
    let object_count = document.createElement("label");
    object_count.innerText = 0;
    // Add object image and counter to the object space and then to the grid
    div_object_img.appendChild(object_img);
    counters_col.appendChild(object_name);
    counters_col.appendChild(div_object_img);
    counters_col.appendChild(object_count);
    counters_row.appendChild(counters_col);
    counters_grid.appendChild(counters_row);
    obj++;
  }
}

function SetCounters() {
  setInterval(function () {
    try {
      // Getting counters (json file data)
      fetch("/counters_data", { method: "GET" })
        .then((response) => response.json())
        .then((response) => {
          // Getting grid for change counters value
          let counters_grid = document.getElementById("CountersGrid");
          // Getting elements of grid for change their labels (counters values)
          let counters_elems = counters_grid.getElementsByClassName(
            "col col-row-3"
          );
          // Changng counters values
          let obj_index = 0;
          for (let obj in response) {
            counters_elems[obj_index].lastChild.innerText = response[obj];
            obj_index++;
          }
        });
    } catch (error) {
      console.log(error);
    }
  }, 1000);
}

function SetInfoCpuTemperature() {
  try {
    setInterval(function () {
      let CpuTemperature = document.getElementById("cpu_temperature");
      let ClassName = CpuTemperature.className;
      fetch("/cpu_temperature", { method: "GET" })
        .then((response) => response.json())
        .then((response) => {
          CpuTemperature.innerText = response;
          if (response > 60) {
            ClassName = ClassName.replace(
              ClassName.split(" ")[1],
              "btn-outline-danger"
            );
          } else if (response > 50) {
            ClassName = ClassName.replace(
              ClassName.split(" ")[1],
              "btn-outline-warning"
            );
          } else if (response > 40) {
            ClassName = ClassName.replace(
              ClassName.split(" ")[1],
              "btn-outline-success"
            );
          } else {
            ClassName = ClassName.replace(
              ClassName.split(" ")[1],
              "btn-outline-info"
            );
          }
          CpuTemperature.className = ClassName;
        });
    }, 1000);
  } catch (error) {
    console.log(error);
  }
}

CreateCounters();
SetCounters();
SetInfoCpuTemperature();
updateFrame();
