"""Main entry point for MyBGInfo - BGInfo-like cross-platform tool."""
import argparse
import os

from PIL import Image, ImageDraw, ImageFont

from src.config import load_config
from src.sysinfo import get_info
from src.wallpaper import set_wallpaper


def generate_wallpaper(cfg):
    """Generate the wallpaper image with system information text.

    Args:
        cfg (dict): Configuration dictionary.

    Returns:
        str: Path to the saved output image.
    """
    bg = cfg.get("background_image")
    if bg and os.path.exists(bg):
        img = Image.open(bg).convert("RGB")
    else:
        w, h = 1920, 1080
        img = Image.new("RGB", (w, h), tuple(cfg.get("background_color", [0, 0, 40])))

    draw = ImageDraw.Draw(img)
    font_path = cfg.get("font_path")
    font_size = cfg.get("font_size", 26)

    try:
        font_title = ImageFont.truetype(font_path or "arial.ttf", font_size + 4)
        font_body = ImageFont.truetype(font_path or "arial.ttf", font_size)
    except Exception:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()

    info = get_info()
    fields = cfg.get("fields", list(info.keys()))
    pos = cfg.get("position", {"x": 50, "y": 50})
    x, y = pos["x"], pos["y"]
    spacing = cfg.get("line_spacing", 38)
    title_color = tuple(cfg.get("title_color", [0, 220, 255]))
    text_color = tuple(cfg.get("text_color", [255, 255, 255]))

    draw.text((x, y), "System Information", fill=title_color, font=font_title)
    y += spacing + 10

    for key in fields:
        value = info.get(key, "N/A")
        draw.text((x, y), f"{key}: {value}", fill=text_color, font=font_body)
        y += spacing

    out = cfg.get("output_file", "wallpaper_output.bmp")
    img.save(out)
    return out


def main():
    """Parse arguments and either launch the GUI or generate the wallpaper."""
    parser = argparse.ArgumentParser(description="MyBGInfo - Custom BGInfo Tool")
    parser.add_argument("--gui", action="store_true", help="Launch the GUI configurator")
    args = parser.parse_args()

    if args.gui:
        from src.gui import launch_gui  # noqa: PLC0415

        launch_gui()
    else:
        cfg = load_config()
        out = generate_wallpaper(cfg)
        set_wallpaper(out)
        print(f"Wallpaper updated: {out}")


if __name__ == "__main__":
    main()
