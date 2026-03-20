import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_FILE = BASE_DIR / "config.json"

DEFAULT_CONFIG = {
    "username": "",
    "notification_message": "Next up $subject in $room with $teacher.",
    "timetable": {
        "Monday": {
            "Form": "08:45",
            "Period 1": "08:55",
            "Period 2": "10:05",
            "Period 3": "12:00",
            "Period 4": "13:40",
        },
        "Tuesday": {
            "Form": "08:45",
            "Period 1": "08:55",
            "Period 2": "10:05",
            "Period 3": "11:45",
            "Period 4": "13:40",
        },
        "Wednesday": {
            "Form": "08:45",
            "Period 1": "08:55",
            "Period 2": "10:05",
            "Period 3": "11:45",
            "Period 4": "13:40",
        },
        "Thursday": {
            "Form": "08:45",
            "Period 1": "08:55",
            "Period 2": "10:05",
            "Period 3": "12:00",
            "Period 4": "13:40",
        },
        "Friday": {
            "Form": "08:45",
            "Period 1": "08:55",
            "Period 2": "10:05",
            "Period 3": "12:00",
            "Period 4": "13:40",
        },
    },
}


def load_config():
    """Loads the config.json file and create a default one if the file dosnt exist.

    Returns:
        dict: The config data loaded from config.json or the default config if the file dose not exist.
    """
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        return DEFAULT_CONFIG

    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
    return config


def update_config(setting, new_value):
    """updates specified value in config.json with the new value.

    Args:
        setting (str): The key you want to change.
        new_value (str): The value you want to replace it with.
    """
    data = load_config()

    data[setting] = new_value

    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)
