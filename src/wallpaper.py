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
    """Set wallpaper on macOS, trying multiple methods."""
    # Method 1: System Events (works on macOS 10.14+, sets all desktops)
    try:
        script = (
            'tell application "System Events"\n'
            '    set desktopCount to count of desktops\n'
            '    repeat with desktopNumber from 1 to desktopCount\n'
            '        tell desktop desktopNumber\n'
            f'            set picture to POSIX file "{path}"\n'
            '        end tell\n'
            '    end repeat\n'
            'end tell'
        )
        subprocess.run(["osascript", "-e", script], check=True, timeout=10)
        return
    except Exception:
        pass

    # Method 2: Finder (legacy fallback)
    try:
        script = f'tell application "Finder" to set desktop picture to POSIX file "{path}"'
        subprocess.run(["osascript", "-e", script], check=True, timeout=10)
        return
    except Exception:
        pass

    # Method 3: wallpaper CLI (if installed via Homebrew)
    try:
        subprocess.run(["wallpaper", "set", path], check=True, timeout=10)
    except (FileNotFoundError, Exception):
        pass


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
    elif "MATE" in desktop:
        subprocess.run(
            ["gsettings", "set", "org.mate.background", "picture-filename", path],
            check=True,
        )
    elif "CINNAMON" in desktop or "X-CINNAMON" in desktop:
        subprocess.run(
            [
                "gsettings", "set",
                "org.cinnamon.desktop.background", "picture-uri",
                f"file://{path}",
            ],
            check=True,
        )
    elif "LXDE" in desktop or "LXQT" in desktop:
        try:
            subprocess.run(["pcmanfm", "--set-wallpaper", path], check=True)
        except FileNotFoundError:
            pass
    elif (
        "SWAY" in desktop
        or os.environ.get("WAYLAND_DISPLAY", "").upper()
        or "HYPRLAND" in desktop
    ):
        if "HYPRLAND" in desktop:
            try:
                subprocess.run(
                    ["hyprctl", "hyprpaper", "wallpaper", f",{path}"], check=True
                )
                return
            except FileNotFoundError:
                pass
        # Try swww first (supports animations), then swaybg
        try:
            subprocess.run(["swww", "img", path], check=True)
            return
        except FileNotFoundError:
            pass
        try:
            subprocess.run(["swaybg", "-i", path, "-m", "fill"], check=True)
            return
        except FileNotFoundError:
            pass
    else:
        # Fallback: try feh, then nitrogen
        try:
            subprocess.run(["feh", "--bg-scale", path], check=True)
        except FileNotFoundError:
            try:
                subprocess.run(["nitrogen", "--set-scaled", path], check=True)
            except FileNotFoundError:
                print(
                    "Could not set wallpaper: no supported tool found.",
                    file=sys.stderr,
                )
