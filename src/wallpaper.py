"""Cross-platform wallpaper setter for MyBGInfo."""
import os
import platform
import subprocess
import sys


def set_wallpaper(path):
    """Set the desktop wallpaper to the given image path."""
    abs_path = os.path.abspath(path)
    system = platform.system()

    if system == "Windows":
        _set_wallpaper_windows(abs_path)
    elif system == "Darwin":
        _set_wallpaper_macos(abs_path)
    elif system == "Linux":
        _set_wallpaper_linux(abs_path)
    else:
        print(f"Unsupported platform: {system}", file=sys.stderr)


def _set_wallpaper_windows(path):
    """Set wallpaper on Windows using ctypes."""
    import ctypes

    SPI_SETDESKWALLPAPER = 0x0014
    SPIF_UPDATEINIFILE = 0x01
    SPIF_SENDCHANGE = 0x02
    ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER, 0, path, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
    )


def _set_wallpaper_macos(path):
    """Set wallpaper on macOS using osascript."""
    script = (
        f'tell application "Finder" to set desktop picture to POSIX file "{path}"'
    )
    subprocess.run(["osascript", "-e", script], check=True)


def _set_wallpaper_linux(path):
    """Set wallpaper on Linux, detecting the desktop environment."""
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").upper()

    if "GNOME" in desktop or "UNITY" in desktop or "PANTHEON" in desktop:
        subprocess.run(
            [
                "gsettings",
                "set",
                "org.gnome.desktop.background",
                "picture-uri",
                f"file://{path}",
            ],
            check=True,
        )
        # Also set for dark mode
        subprocess.run(
            [
                "gsettings",
                "set",
                "org.gnome.desktop.background",
                "picture-uri-dark",
                f"file://{path}",
            ],
            check=False,
        )
    elif "KDE" in desktop:
        script = f"""
var allDesktops = desktops();
for (var i = 0; i < allDesktops.length; i++) {{
    var d = allDesktops[i];
    d.wallpaperPlugin = "org.kde.image";
    d.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    d.writeConfig("Image", "file://{path}");
}}
"""
        subprocess.run(
            [
                "qdbus",
                "org.kde.plasmashell",
                "/PlasmaShell",
                "org.kde.PlasmaShell.evaluateScript",
                script,
            ],
            check=True,
        )
    elif "XFCE" in desktop:
        subprocess.run(
            [
                "xfconf-query",
                "--channel", "xfce4-desktop",
                "--property", "/backdrop/screen0/monitor0/workspace0/last-image",
                "--set", path,
            ],
            check=True,
        )
    else:
        # Fallback: try feh
        try:
            subprocess.run(["feh", "--bg-scale", path], check=True)
        except FileNotFoundError:
            print(
                "Could not set wallpaper: unsupported desktop environment "
                "and 'feh' is not installed.",
                file=sys.stderr,
            )
