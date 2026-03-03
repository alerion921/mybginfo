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

try:
    import GPUtil
    _HAS_GPUTIL = True
except ImportError:
    _HAS_GPUTIL = False

try:
    from screeninfo import get_monitors
    _HAS_SCREENINFO = True
except ImportError:
    _HAS_SCREENINFO = False


def get_windows_version_name(version_str: str, build_number: int) -> str:
    """Map a Windows version string and build number to a friendly name.

    Args:
        version_str: The NT version string (e.g. "5.1", "10.0").
        build_number: The OS build number (e.g. 22621).

    Returns:
        A friendly Windows version name such as "Windows 11".
    """
    parts = version_str.split(".")
    major = int(parts[0]) if parts else 0
    minor = int(parts[1]) if len(parts) > 1 else 0

    if major == 5 and minor == 0:
        return "Windows 2000"
    if major == 5 and minor in (1, 2):
        return "Windows XP"
    if major == 6 and minor == 0:
        return "Windows Vista"
    if major == 6 and minor == 1:
        return "Windows 7"
    if major == 6 and minor == 2:
        return "Windows 8"
    if major == 6 and minor == 3:
        return "Windows 8.1"
    if major == 10:
        if build_number >= 26100:
            return "Windows 12"
        if build_number >= 22000:
            return "Windows 11"
        if build_number >= 10240:
            return "Windows 10"
    return f"Windows NT {major}.{minor}"


def _get_screen_resolution() -> str:
    """Return the primary display resolution as 'WxH', or 'N/A'."""
    if _HAS_SCREENINFO:
        try:
            monitors = get_monitors()
            if monitors:
                m = monitors[0]
                return f"{m.width}\u00d7{m.height}"
        except Exception:
            pass
    if platform.system() == "Windows":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            w = user32.GetSystemMetrics(0)
            h = user32.GetSystemMetrics(1)
            if w and h:
                return f"{w}\u00d7{h}"
        except Exception:
            pass
    return "N/A"


def get_info() -> dict:
    """Return a dict of system information fields (always fresh values)."""
    info = {}

    # Hostname
    info["Hostname"] = socket.gethostname()

    # Current user
    info["User"] = os.environ.get("USER") or os.environ.get("USERNAME") or "Unknown"

    # OS friendly name
    system = platform.system()
    if system == "Windows":
        try:
            ver = platform.version()  # e.g. "10.0.22621"
            ver_parts = ver.split(".")
            build = int(ver_parts[2]) if len(ver_parts) > 2 else 0
            nt_ver = f"{ver_parts[0]}.{ver_parts[1]}" if len(ver_parts) > 1 else ver_parts[0]
            friendly = get_windows_version_name(nt_ver, build)
            info["OS"] = f"{friendly} (Build {build})"
        except Exception:
            info["OS"] = f"Windows {platform.release()}"
    else:
        info["OS"] = f"{system} {platform.release()}"

    # CPU model
    info["CPU"] = platform.processor() or "Unknown"

    if _HAS_PSUTIL:
        # CPU core count
        info["CPU Cores"] = str(psutil.cpu_count(logical=True))

        # CPU usage (non-blocking; first call may return 0.0 which is acceptable)
        try:
            info["CPU Usage"] = f"{psutil.cpu_percent(interval=None):.0f}%"
        except Exception:
            info["CPU Usage"] = "N/A"

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

        # Uptime
        try:
            boot_ts = psutil.boot_time()
            uptime_secs = int(datetime.datetime.now().timestamp() - boot_ts)
            days, rem = divmod(uptime_secs, 86400)
            hours, rem = divmod(rem, 3600)
            minutes = rem // 60
            info["Uptime"] = f"{days}d {hours}h {minutes}m"
        except Exception:
            info["Uptime"] = "N/A"

        # Network sent / received
        try:
            net = psutil.net_io_counters()
            info["Network Sent"] = f"{net.bytes_sent / (1024 ** 2):.1f} MB"
            info["Network Recv"] = f"{net.bytes_recv / (1024 ** 2):.1f} MB"
        except Exception:
            info["Network Sent"] = "N/A"
            info["Network Recv"] = "N/A"
    else:
        info["CPU Cores"] = "N/A"
        info["CPU Usage"] = "N/A"
        info["RAM"] = "N/A"
        info["RAM Used"] = "N/A"
        info["Disk Total"] = "N/A"
        info["Disk Used"] = "N/A"
        info["Boot Time"] = "N/A"
        info["Uptime"] = "N/A"
        info["Network Sent"] = "N/A"
        info["Network Recv"] = "N/A"

    # GPU
    if _HAS_GPUTIL:
        try:
            gpus = GPUtil.getGPUs()
            info["GPU"] = gpus[0].name if gpus else "N/A"
        except Exception:
            info["GPU"] = "N/A"
    else:
        info["GPU"] = "N/A"

    # Screen resolution
    info["Screen Resolution"] = _get_screen_resolution()

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
