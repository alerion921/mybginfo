"""Configuration loader and saver for MyBGInfo."""
import json
import os

DEFAULT_CONFIG = {
    "background_image": "assets/default_bg.jpg",
    "output_file": "wallpaper_output.bmp",
    "text_color": [255, 255, 255],
    "title_color": [0, 220, 255],
    "background_color": [0, 0, 40],
    "font_path": None,
    "font_size": 26,
    "position": {"x": 50, "y": 50},
    "line_spacing": 38,
    "fields": [
        "Hostname", "User", "OS", "CPU", "RAM", "RAM Used",
        "Disk Total", "Disk Used", "IP Address", "Boot Time", "Date/Time"
    ],
}


def load_config(path="config/bginfo.json"):
    """Load configuration from JSON file, merging with defaults."""
    if os.path.exists(path):
        with open(path, "r") as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    return DEFAULT_CONFIG.copy()


def save_config(cfg, path="config/bginfo.json"):
    """Save configuration to JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)
