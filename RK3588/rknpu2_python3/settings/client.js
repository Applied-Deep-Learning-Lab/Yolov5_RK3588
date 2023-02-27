onchangeCallbacks = {
  "colored": "color_select()"
}

async function replaceSettings() {
  form = document.getElementById("settings")
  form.innerHTML = '<div class="loading_msg"><p>LOADING...</p></div>'
  form.innerHTML = await deploySettings()
  color_select()
}

async function getSettings() {

  response = await fetch("/settings", {method: 'GET', headers: {'Content-Type': 'application/json'}})
  out = await response.json()
  jsonOut = JSON.parse(out)
  return jsonOut
}

function retrieveRadio(name){
  var radios = document.getElementsByName(name);
  for (var i = 0, length = radios.length; i < length; i++) {
    if (radios[i].checked) {
      return radios[i].value;
    }
  }
}

function retrieveValue(name){
  return document.getElementById(name).value
}

function retrieveCheckbox(name){
  return document.getElementById(name).checked
}

function retrieveTextArea(name){
  var words = retrieveValue(name).split(",")
  return words.map(element => {
    return element.trim();
  });
}

function updateSettings(){
  for(setting of settings){
    for(child of setting["childs"]){
      switch(child["tag"]){
        case "radio":
          child["value"] = retrieveRadio(child["name"])
        break;
        case "select":
        case "number":
          child["value"] = retrieveValue(child["name"])
          break;
        case "checkbox":
          child["value"] = retrieveCheckbox(child["name"])
        break;
        case "textarea":
          child["value"] = retrieveTextArea(child["name"])
        break;
        default:
        break;
      }
    }
  }
  postSettings(settings)
  replaceSettings()
}

function postSettings(settings){
  fetch("/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings)
  }).then((response) => {
  })
}

function deployLabel(name, label){
  if(typeof(label) !== 'undefined'){
    return "<th class='label'><label for='" + name + "'>" + label + "</label></th>"
  }
  else{
    return ""
  }
}

function deployRadioButton(radio){
  var radioHTML = ""
  var col = 0
  for(option of radio["options"]){
    if (col == 2){
      radioHTML += "</tr><tr>"
      col = 0
    }
    var checked = ""
    if (radio["value"] == option[0]){
      checked = "checked"
    }

    radioHTML += deployLabel(option[0], option[1])
    radioHTML += "<td class='content'><input type='radio' name='" + radio["name"] + "' value='" + option[0] + "' id='" + option[0] + "' "+ checked + "></td></input>"
    col += 1
  }
  return radioHTML
}

function deployTextArea(textarea){
  return "<td class='content' colspan=3><textarea cols=50 rows=1 id='" + textarea["name"] +"' onkeyup='textAreaAdjust(this)'>" + textarea["value"] + "</textarea></td>"
}

function deployTextField(textfield){
  return "<td class='content'><input type='text' id=" + textfield["name"] + " value=" + textfield["value"] + "></input></td>"
}

function deployCheckBox(checkbox){
  var checked = ""
  if(checkbox["value"]){
    checked = "checked"
  }
  return "<td class='content'><input type='checkbox' id=" + checkbox["name"] + " " + checked  + "></input></td>"
}

function deployNumber(number){
  return "<td class='content'><input type='number' step='" + number["step"] + "' max = '" + number["max"] + "' min = '" + number["min"] + "' value = '" + number["value"] + "' id='" + number["name"] + "'>"  + "</input></td>"
}

function deploySelect(select){
  var cls = ""
  var onchange = ""
  var tag = document.createElement("select")
  var th = document.createElement("th")
  tag.className = select['class']
  tag.id = select["name"]
  if(select["class"] in onchangeCallbacks){
    tag.setAttribute("onchange", onchangeCallbacks[select["class"]])
  }
  var options = []
  for (option of select["options"]){
    var opt = document.createElement("option")
    opt.value = option
    opt.style = 'color: ' + option
    opt.innerHTML = option
    if (select["value"] != option){
      options.push(opt)
    }
    else{
      chosen_option = opt
    }
  }
  tag.appendChild(chosen_option)
  for (opt of options){
    tag.appendChild(opt)
  }
  tag.value = select["options"][0]
  th.appendChild(tag)
  return th.outerHTML
}

function deployChild(child){
  var tag = null
  switch(child["tag"]){
    case "radio":
      tag = deployRadioButton(child)
      break;
    case "textarea":
      tag = deployTextArea(child)
      break;
    case "checkbox":
      tag = deployCheckBox(child)
      break;
    case "number":
      tag = deployNumber(child)
      break;
    case "select":
      tag = deploySelect(child)
      break;
    case "textfield":
      tag = deployTextField(child)
  }
  if (tag != null){
    return deployLabel(child["name"], child["label"]) + tag
  }
  else {
    return ""
  }
}

async function deploySettings() {
  settings = await getSettings()
  var settingsHTML = ""
  settingsHTML += "<button id='upd_settings' onclick='updateSettings()' style='text-align: center'>Update Settings</button><div id='setting_tables'>"
  for(setting of settings){
    settingsHTML += "<table><tr><th class='header' colspan=4>" + setting["label"] + "</th></tr><tr>"
    col = 0
    for(child of setting["childs"]){
      if (col == 2 || child["tag"] == "textarea"){
        settingsHTML += "</tr><tr>"
        col = 0
      }
      settingsHTML += deployChild(child)
      col += 1 
    }
    settingsHTML += "</table>"
  }
  settingsHTML += "</div><button id='upd_settings' onclick='updateSettings()' style='text-align: center'>Update Settings</button></th></tr>"
  return settingsHTML
}

function color_select(){
  selects = document.getElementsByClassName("colored")
  for(var i=0, max=selects.length; i < max; i++){
    selects[i].style.color = selects[i].options[selects[i].selectedIndex].style.color;
  }
}
function textAreaAdjust(element) {
  element.style.height = "1px";
  element.style.height = (25+element.scrollHeight)+"px";
}

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); // $& means the whole matched string
}
