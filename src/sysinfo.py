"""System information gatherer for MyBGInfo."""
import datetime
import os
import platform
import socket

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False


def get_info():
    """Return a dict of system information fields."""
    info = {}

    # Hostname
    info["Hostname"] = socket.gethostname()

    # Current user
    info["User"] = os.environ.get("USER") or os.environ.get("USERNAME") or "Unknown"

    # OS name and version
    info["OS"] = platform.system()
    info["Version"] = platform.version()

    # CPU model
    info["CPU"] = platform.processor() or "Unknown"

    if _HAS_PSUTIL:
        # CPU core count
        info["CPU Cores"] = str(psutil.cpu_count(logical=True))

        # RAM total / used
        mem = psutil.virtual_memory()
        info["RAM"] = f"{mem.total / (1024 ** 3):.1f} GB"
        info["RAM Used"] = f"{mem.used / (1024 ** 3):.1f} GB ({mem.percent}%)"

        # Disk total / used for the system drive
        try:
            system_root = os.path.splitdrive(os.path.expanduser("~"))[0] or "/"
            if not system_root.endswith(os.sep):
                system_root += os.sep
            disk = psutil.disk_usage(system_root)
            info["Disk Total"] = f"{disk.total / (1024 ** 3):.1f} GB"
            info["Disk Used"] = f"{disk.used / (1024 ** 3):.1f} GB ({disk.percent}%)"
        except Exception:
            info["Disk Total"] = "N/A"
            info["Disk Used"] = "N/A"

        # Boot time
        try:
            boot_ts = psutil.boot_time()
            info["Boot Time"] = datetime.datetime.fromtimestamp(boot_ts).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        except Exception:
            info["Boot Time"] = "N/A"
    else:
        info["CPU Cores"] = "N/A"
        info["RAM"] = "N/A"
        info["RAM Used"] = "N/A"
        info["Disk Total"] = "N/A"
        info["Disk Used"] = "N/A"
        info["Boot Time"] = "N/A"

    # IP address
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            info["IP Address"] = s.getsockname()[0]
    except Exception:
        info["IP Address"] = "N/A"

    # Current date/time
    info["Date/Time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return info
