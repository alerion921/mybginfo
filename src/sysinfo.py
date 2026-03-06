"""System information gatherer for MyBGInfo."""
import datetime
import os
import platform
import socket
import subprocess

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
    import pynvml
    _HAS_PYNVML = True
except ImportError:
    _HAS_PYNVML = False

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
        if build_number >= 22000:
            return "Windows 11"
        if build_number >= 10240:
            return "Windows 10"
    return f"Windows NT {major}.{minor}"


def _get_windows_os_name() -> str:
    """Read the friendly OS name from the Windows registry.

    Returns:
        A string like "Windows 11 23H2", or an empty string on failure.
    """
    try:
        import winreg  # noqa: PLC0415
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion",
        )
        product_name = winreg.QueryValueEx(key, "ProductName")[0]
        try:
            display_version = winreg.QueryValueEx(key, "DisplayVersion")[0]
        except OSError:
            display_version = ""
        # Read the actual build number to correct the product name if needed
        try:
            build_str = winreg.QueryValueEx(key, "CurrentBuildNumber")[0]
            build_number = int(build_str)
        except (OSError, ValueError):
            build_number = 0

        # Fix: ProductName may say "Windows 10" even on Windows 11 (build >= 22000)
        if build_number >= 22000 and "Windows 10" in product_name:
            product_name = product_name.replace("Windows 10", "Windows 11")

        if display_version:
            return f"{product_name} {display_version}"
        return product_name
    except Exception:
        return ""


def _get_cpu_name() -> str:
    """Return a friendly CPU model name.

    On Windows, reads from the registry (ProcessorNameString).
    Falls back to ``platform.processor()`` on any failure or non-Windows OS.
    """
    if platform.system() == "Windows":
        try:
            import winreg  # noqa: PLC0415
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
            )
            return winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
        except Exception:
            pass
    return platform.processor() or "Unknown"


def _get_gpu_name() -> str:
    """Return the primary GPU name using platform-native commands.

    Windows: pynvml (NVIDIA) -> wmic -> PowerShell; Linux: lspci; macOS: system_profiler.
    Falls back gracefully to "Unknown".
    """
    system = platform.system()
    try:
        if system == "Windows":
            # First try pynvml for NVIDIA GPUs
            if _HAS_PYNVML:
                try:
                    pynvml.nvmlInit()
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    name = pynvml.nvmlDeviceGetName(handle)
                    if isinstance(name, bytes):
                        name = name.decode()
                    pynvml.nvmlShutdown()
                    return name
                except Exception:
                    try:
                        pynvml.nvmlShutdown()
                    except Exception:
                        pass
            # Then try wmic
            try:
                result = subprocess.check_output(
                    ["wmic", "path", "win32_VideoController", "get", "Name"],
                    stderr=subprocess.DEVNULL,
                ).decode(errors="ignore")
                lines = [
                    line.strip()
                    for line in result.strip().splitlines()
                    if line.strip() and line.strip().lower() != "name"
                ]
                if lines:
                    return lines[0]
            except Exception:
                pass
            # Finally try PowerShell as fallback
            try:
                result = subprocess.check_output(
                    ["powershell", "-NoProfile", "-Command",
                     "Get-WmiObject Win32_VideoController | Select-Object -ExpandProperty Name"],
                    stderr=subprocess.DEVNULL,
                ).decode(errors="ignore")
                lines = [
                    line.strip()
                    for line in result.strip().splitlines()
                    if line.strip()
                ]
                if lines:
                    return lines[0]
            except Exception:
                pass
            return "Unknown"
        if system == "Linux":
            result = subprocess.check_output(
                ["lspci"],
                stderr=subprocess.DEVNULL,
            ).decode(errors="ignore")
            for line in result.splitlines():
                lower = line.lower()
                if "vga" in lower or "3d" in lower or "display" in lower:
                    # Strip the PCI address prefix, keep the device name
                    parts = line.split(":", 2)
                    return parts[-1].strip() if parts else line.strip()
            return "Unknown"
        if system == "Darwin":
            result = subprocess.check_output(
                ["system_profiler", "SPDisplaysDataType"],
                stderr=subprocess.DEVNULL,
            ).decode(errors="ignore")
            for line in result.splitlines():
                if "Chipset Model" in line or "Graphics" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2 and parts[1].strip():
                        return parts[1].strip()
            return "Unknown"
    except Exception:
        pass
    # Final fallback: try GPUtil if available
    if _HAS_GPUTIL:
        try:
            gpus = GPUtil.getGPUs()
            return gpus[0].name if gpus else "Unknown"
        except Exception:
            pass
    return "Unknown"


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
        friendly = _get_windows_os_name()
        if not friendly:
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
            info["OS"] = friendly
    else:
        info["OS"] = f"{system} {platform.release()}"

    # CPU model
    info["CPU"] = _get_cpu_name()

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

        # Disk total / used / free for the system drive
        try:
            system_root = os.path.splitdrive(os.path.expanduser("~"))[0] or "/"
            if not system_root.endswith(os.sep):
                system_root += os.sep
            disk = psutil.disk_usage(system_root)
            info["Disk Total"] = f"{disk.total / (1024 ** 3):.1f} GB"
            info["Disk Used"] = f"{disk.used / (1024 ** 3):.1f} GB ({disk.percent}%)"
            info["Disk Free"] = f"{disk.free / (1024 ** 3):.1f} GB"
        except Exception:
            info["Disk Total"] = "N/A"
            info["Disk Used"] = "N/A"
            info["Disk Free"] = "N/A"

        # All mounted disk partitions
        try:
            parts = []
            for part in psutil.disk_partitions(all=False):
                if "cdrom" in part.opts or part.fstype == "":
                    continue
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    parts.append(
                        f"{part.mountpoint}  {usage.used / (1024 ** 3):.1f} GB"
                        f" / {usage.total / (1024 ** 3):.1f} GB ({usage.percent}%)"
                    )
                except PermissionError:
                    continue
            info["All Disks"] = "\n".join(parts) if parts else "N/A"
        except Exception:
            info["All Disks"] = "N/A"

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
        info["Disk Free"] = "N/A"
        info["All Disks"] = "N/A"
        info["Boot Time"] = "N/A"
        info["Uptime"] = "N/A"
        info["Network Sent"] = "N/A"
        info["Network Recv"] = "N/A"

    # GPU name
    info["GPU"] = _get_gpu_name()

    # GPU usage / temperature (via GPUtil or pynvml)
    if _HAS_GPUTIL:
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                info["GPU Usage"] = f"{gpus[0].load * 100:.0f}%"
                info["GPU Temp"] = f"{gpus[0].temperature:.0f}°C"
            else:
                info["GPU Usage"] = "N/A"
                info["GPU Temp"] = "N/A"
        except Exception:
            info["GPU Usage"] = "N/A"
            info["GPU Temp"] = "N/A"
    elif _HAS_PYNVML:
        try:
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            pynvml.nvmlShutdown()
            info["GPU Usage"] = f"{util.gpu}%"
            info["GPU Temp"] = f"{temp}°C"
        except Exception:
            try:
                pynvml.nvmlShutdown()
            except Exception:
                pass
            info["GPU Usage"] = "N/A"
            info["GPU Temp"] = "N/A"
    else:
        info["GPU Usage"] = "N/A"
        info["GPU Temp"] = "N/A"

    # CPU temperature (Linux/macOS; Windows rarely exposes this without 3rd-party drivers)
    # Sensor key priority: Intel (coretemp), AMD (k10temp), ARM (cpu_thermal), ACPI (acpitz)
    try:
        temps = psutil.sensors_temperatures() if _HAS_PSUTIL else {}
        cpu_temp_found = False
        for key in ("coretemp", "k10temp", "cpu_thermal", "acpitz"):
            if key in temps and temps[key]:
                t = temps[key][0].current
                info["CPU Temp"] = f"{t:.0f}°C"
                cpu_temp_found = True
                break
        if not cpu_temp_found:
            info["CPU Temp"] = "N/A"
    except (AttributeError, Exception):
        info["CPU Temp"] = "N/A"

    # Screen resolution
    info["Screen Resolution"] = _get_screen_resolution()

    # IP address
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            info["IP Address"] = local_ip
    except Exception:
        info["IP Address"] = "N/A"
        local_ip = None

    # Active network interface
    try:
        if local_ip and _HAS_PSUTIL:
            for iface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.address == local_ip:
                        info["Network Interface"] = iface
                        break
                else:
                    continue
                break
            else:
                info["Network Interface"] = "N/A"
        else:
            info["Network Interface"] = "N/A"
    except Exception:
        info["Network Interface"] = "N/A"

    # Public IP address
    try:
        import urllib.request  # noqa: PLC0415
        with urllib.request.urlopen("https://api.ipify.org", timeout=3) as resp:
            info["Public IP"] = resp.read().decode().strip()
    except Exception:
        info["Public IP"] = "N/A"

    # Local timezone
    try:
        import time as _time  # noqa: PLC0415
        info["Timezone"] = _time.strftime("%Z (UTC%z)")
    except Exception:
        info["Timezone"] = "N/A"

    # Current date/time
    info["Date/Time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return info
