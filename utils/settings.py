import json
import os

SETTINGS_FILE = "ring_settings.json"


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return default_settings()

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default_settings()


def default_settings():
    return {
        "sigma": 2,
        "upscale": 2,
        "psy_weight": 0.3,
        "contrast": 1.0,
        "preset": "default"
    }