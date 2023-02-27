import json
import os
from modules import config

ROOT = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(ROOT, 'settings.json')
SETTINGS_PATH_TEMP = os.path.join(ROOT, 'settings.json')

TO_CORRECT = ["inference", "counting", "camera", "scale"] # Settings blocks to correct after aplying


def adjust_by_words(textarea):
    """
    Adjust textarea by maxwords
        Parameters:
            textarea(dict("tag":"textarea", ["name", "label",  "maxwords", "value"])) 
                - Text Area from settings dictionary
        Returns:
            text(str) - Text form text area adjusted by max words length
    """
    try:
        textarea["value"].remove('')
    except:
        pass
    return textarea["value"][:textarea["maxwords"]]


def adjust_by_extremums(number):
    """
    Adjust number by extremums
        Parameters:
            number(dict("tag":"number", ["name", "label", "max", "min", "step", "value"])) 
                - Number from settings dictionary
        Returns:
            num(int/float) - Number adjusted by extremums
    """
    number["value"] = float(number["value"])
    num = number["max"] if number["value"] > number["max"] else number["value"] \
        if number["value"] > number["min"] else number["min"]
    if int(number["step"]) == 1:
        return int(num)
    else:
        return num


def adjust_settings(settings_json):
    """
    Adjust settings parameters
        Parameters:
            settings_json(dict) - Settings dictionary
        Returns:
            settings_json(dict) - Adjusted settings dictionary
    """
    for sett in settings_json:
        for child in sett["childs"]:
            if child["tag"] == "textarea":
                child["value"] = adjust_by_words(child)
            elif child["tag"] == "number":
                child["value"] = adjust_by_extremums(child)
    return settings_json


def load_settings(settings="./settings/settings.json"):
    """
    Load settings from file or from serialized json
    """
    if not isinstance(settings, str):               # If settings is not path
        settings_json = adjust_settings(settings)       # Adjust got settings
        with open(SETTINGS_PATH_TEMP, 'w') as f:
            json.dump(settings_json, f, indent=2)       # Save new settings to file
        settings = SETTINGS_PATH_TEMP
    settings_json = json.load(open(settings)) # Load json files containing list of objects

    settings = {}
    for category in settings_json:     # Retrieveng settings from json
        settings[category["name"]] = {}     # Make dictionary for category
        for prop in category["childs"]:     
            settings[category["name"]][prop["name"]] = prop["value"] # Fill dictionary with chilren values
    
    # Defining list of class names
    all_ids = [i for i in range(80)]
    if settings["classes"]["mode"] == "coco":
        settings["classes"]["list"] = list(config.CLASSES)  # Refer constants.py for coco_classes
    elif settings["classes"]["mode"] == "ids":
        settings["classes"]["list"] = all_ids       # Set ids as class names
    elif settings["classes"]["mode"] == "custom":
        settings["classes"]["list"].extend([f"{i}" for i in range(80 - len(settings["classes"]["list"]))])
    else:
        classes = []

    if not len(settings["classes"]["to_display"]): # If list of classes to dislplay is empty:
        to_display = all_ids                            # Display all classes
    else:
        to_display = []                             # Else:
        for i in settings["classes"]["to_display"]: # Convert list of strings list to integers
            try:                                     
                to_display.append(int(i))               # Try to parse id and add to list
            except ValueError:                              
                try:                                    # If value is not id, but class name 
                    to_display.append(classes.index(i))     # retrieve and add class id to list
                except:                                 # If value is not id nor valid class name
                    continue                                # Go to next value
    settings["classes"]["to_display"] = to_display
    return settings


def save_corrected_settings(corrected_settings):
    """
    Save corrected settings to file
        Parameters:
            corrected_settings(dict): Settings dictionary corrected after applying
    """
    settings_json = json.load(open(SETTINGS_PATH))
    for sett in settings_json:
        if sett["name"] in TO_CORRECT:
            for child in sett["childs"]:
                child["value"] = corrected_settings[sett["name"]][child["name"]]

    with open(SETTINGS_PATH, 'w') as f:
            json.dump(settings_json, f, indent=2)
