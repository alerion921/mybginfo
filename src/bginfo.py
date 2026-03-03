"""Main entry point for MyBGInfo - BGInfo-like cross-platform tool."""
import argparse
import datetime
import os
import threading
import time

from PIL import Image, ImageDraw, ImageFont

from src.config import load_config
from src.sysinfo import get_info
from src.wallpaper import set_wallpaper


def generate_wallpaper(cfg: dict) -> str:
    """Generate the wallpaper image with system information text.

    Args:
        cfg: Configuration dictionary.

    Returns:
        Path to the saved output image.
    """
    bg = cfg.get("background_image")
    if bg and os.path.exists(bg):
        img = Image.open(bg).convert("RGB")
    else:
        w, h = 1920, 1080
        img = Image.new("RGB", (w, h), tuple(cfg.get("background_color", [0, 0, 40])))

    img_width, img_height = img.size

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
    spacing = cfg.get("line_spacing", 38)

    title_color = tuple(cfg.get("title_color", [0, 220, 255]))
    label_color = tuple(cfg.get("label_color", [180, 180, 255]))
    value_color = tuple(cfg.get("value_color", [255, 255, 255]))
    shadow_color = tuple(cfg.get("shadow_color", [0, 0, 0]))
    separator_color = tuple(cfg.get("separator_color", [0, 220, 255]))

    use_shadow = cfg.get("shadow", True)
    use_panel = cfg.get("text_bg_panel", False)
    use_separator = cfg.get("separator_line", True)

    title_text = cfg.get("title_text", "System Information")

    alignment = cfg.get("text_alignment", "left")
    margin = cfg.get("text_margin", 50)
    y = cfg.get("position_y", 50)

    # ------------------------------------------------------------------ #
    # Measure max text width to compute X based on alignment              #
    # ------------------------------------------------------------------ #
    dummy_draw = ImageDraw.Draw(img)

    def _text_width(text: str, font) -> int:
        try:
            bb = dummy_draw.textbbox((0, 0), text, font=font)
            return bb[2] - bb[0]
        except Exception:
            return len(text) * font_size

    lines = [(title_text, font_title, True)]
    for key in fields:
        value = info.get(key, "N/A")
        lines.append((f"{key}: {value}", font_body, False))

    max_text_width = max((_text_width(text, fnt) for text, fnt, _ in lines), default=200)

    if alignment == "right":
        x = img_width - max_text_width - margin
    elif alignment == "center":
        x = (img_width - max_text_width) // 2
    else:  # "left"
        x = margin

    x = max(0, x)

    # ------------------------------------------------------------------ #
    # Optional semi-transparent background panel                          #
    # ------------------------------------------------------------------ #
    if use_panel:
        panel_height = spacing + 10 + len(fields) * spacing + 10
        alpha = cfg.get("text_bg_alpha", 160)
        bg_color = tuple(cfg.get("text_bg_color", [0, 0, 20]))
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ov_draw = ImageDraw.Draw(overlay)
        ov_draw.rectangle(
            [x - 8, y - 4, x + max_text_width + 8, y + panel_height],
            fill=(*bg_color, alpha),
        )
        img = img.convert("RGBA")
        img = Image.alpha_composite(img, overlay).convert("RGB")

    draw = ImageDraw.Draw(img)

    # ------------------------------------------------------------------ #
    # Helper to draw optional shadow then text                            #
    # ------------------------------------------------------------------ #
    def _draw_text(px: int, py: int, text: str, fill, font) -> None:
        if use_shadow:
            draw.text((px + 2, py + 2), text, fill=shadow_color, font=font)
        draw.text((px, py), text, fill=fill, font=font)

    # ------------------------------------------------------------------ #
    # Draw title                                                          #
    # ------------------------------------------------------------------ #
    _draw_text(x, y, title_text, title_color, font_title)
    y += spacing + 10

    # Optional separator line
    if use_separator:
        sep_y = y - 6
        draw.line([(x, sep_y), (x + max_text_width, sep_y)], fill=separator_color, width=1)

    # ------------------------------------------------------------------ #
    # Draw fields                                                         #
    # ------------------------------------------------------------------ #
    for key in fields:
        value = info.get(key, "N/A")
        line_text = f"{key}: {value}"
        # Split label / value and colour them individually
        if ": " in line_text:
            label_part, value_part = line_text.split(": ", 1)
            label_str = label_part + ": "
            label_w = _text_width(label_str, font_body)
            _draw_text(x, y, label_str, label_color, font_body)
            _draw_text(x + label_w, y, value_part, value_color, font_body)
        else:
            _draw_text(x, y, line_text, value_color, font_body)
        y += spacing

    out = cfg.get("output_file", "wallpaper_output.bmp")
    img.save(out)
    return out


def start_auto_refresh(
    cfg_path: str = "config/bginfo.json",
    interval: int = 60,
    _last_update: list | None = None,
) -> tuple:
    """Start a background thread that regenerates the wallpaper periodically.

    Args:
        cfg_path: Path to the configuration JSON file.
        interval: Seconds between updates.
        _last_update: Optional list shared with the caller; the worker appends
            the timestamp string of each successful update so callers can
            display the actual last-refresh time.

    Returns:
        A ``(thread, stop_event)`` tuple.  Call ``stop_event.set()`` to stop.
    """
    stop_event = threading.Event()

    def _worker() -> None:
        while not stop_event.is_set():
            try:
                cfg = load_config(cfg_path)
                out = generate_wallpaper(cfg)
                set_wallpaper(out)
                ts = datetime.datetime.now().strftime("%H:%M:%S")
                if _last_update is not None:
                    _last_update.append(ts)
                print(f"[auto-refresh] Wallpaper updated: {out}")
            except Exception as exc:
                print(f"[auto-refresh] Error: {exc}")
            stop_event.wait(interval)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread, stop_event


def main() -> None:
    """Parse arguments and either launch the GUI or generate the wallpaper."""
    parser = argparse.ArgumentParser(description="MyBGInfo - Custom BGInfo Tool")
    parser.add_argument("--gui", action="store_true", help="Launch the GUI configurator")
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        metavar="N",
        help="Auto-refresh interval in seconds (0 to disable; overrides config)",
    )
    args = parser.parse_args()

    if args.gui:
        from src.gui import launch_gui  # noqa: PLC0415

        launch_gui()
    else:
        cfg = load_config()

        # Allow CLI to override refresh_interval
        if args.interval is not None:
            cfg["refresh_interval"] = args.interval

        interval = cfg.get("refresh_interval", 0)
        if interval and interval > 0:
            _, stop_event = start_auto_refresh(interval=interval)
            print(f"Auto-refresh started (every {interval}s). Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                stop_event.set()
                print("Auto-refresh stopped.")
        else:
            out = generate_wallpaper(cfg)
            set_wallpaper(out)
            print(f"Wallpaper updated: {out}")


if __name__ == "__main__":
    main()
