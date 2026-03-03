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
    "line_spacing": 38,
    "fields": [
        "Hostname", "User", "OS", "CPU", "RAM", "RAM Used",
        "Disk Total", "Disk Used", "IP Address", "Boot Time", "Date/Time"
    ],
    # Layout / alignment
    "text_alignment": "left",   # "left" | "center" | "right"
    "text_margin": 50,          # pixels from the chosen screen edge
    "position_y": 50,           # vertical offset from top
    # Refresh
    "refresh_interval": 60,     # seconds between live updates (0 = disabled)
    # Shadow
    "shadow": True,
    "shadow_color": [0, 0, 0],
    # Text background panel
    "text_bg_panel": False,
    "text_bg_alpha": 160,       # 0-255 alpha for the panel
    "text_bg_color": [0, 0, 20],
    # Separator line under title
    "separator_line": True,
    "separator_color": [0, 220, 255],
    # Title
    "title_text": "System Information",
    # Per-role colours
    "label_color": [180, 180, 255],
    "value_color": [255, 255, 255],
}


def load_config(path="config/bginfo.json"):
    """Load configuration from JSON file, merging with defaults.

    Backward-compatible: keys missing from a saved file fall back to defaults.
    The legacy ``position`` dict (``{"x": …, "y": …}``) is migrated to the new
    ``text_margin`` / ``position_y`` keys automatically.
    """
    if os.path.exists(path):
        with open(path, "r") as f:
            saved = json.load(f)
        # Migrate legacy position dict – `saved` is a fresh local dict from JSON, safe to mutate
        if "position" in saved and "text_margin" not in saved:
            pos = saved.pop("position")
            saved.setdefault("text_margin", pos.get("x", 50))
            saved.setdefault("position_y", pos.get("y", 50))
        return {**DEFAULT_CONFIG, **saved}
    return DEFAULT_CONFIG.copy()


def save_config(cfg, path="config/bginfo.json"):
    """Save configuration to JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)
