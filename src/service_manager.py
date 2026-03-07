"""Windows service manager for MyBGInfo.

Requires pywin32 (``pip install pywin32``).  This module is a no-op on
non-Windows platforms; the service class is only defined when pywin32 is
available.
"""
import os
import platform
import sys
import time

SERVICE_NAME = "MyBGInfoService"
SERVICE_DISPLAY = "MyBGInfo Background Refresher"

# Project root directory (two levels up from this file: src/ -> project root)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run_elevated(action: str) -> None:
    """Request elevation via runas and invoke this module with *action*."""
    import ctypes  # noqa: PLC0415
    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        f"-m src.service_manager {action}",
        _PROJECT_ROOT,   # lpDirectory – ensures package imports resolve
        1,
    )


def _do_install() -> None:
    """Actually install (with auto-start) and start the service (must run elevated)."""
    import win32service  # noqa: PLC0415
    import win32serviceutil  # noqa: PLC0415
    win32serviceutil.InstallService(
        pythonClassString="src.service_manager.MyBGInfoService",
        serviceName=SERVICE_NAME,
        displayName=SERVICE_DISPLAY,
        startType=win32service.SERVICE_AUTO_START,
        exeName=sys.executable,
    )
    win32serviceutil.StartService(SERVICE_NAME)


def _do_remove() -> None:
    """Actually stop and remove the service (must run elevated)."""
    import win32serviceutil  # noqa: PLC0415
    try:
        win32serviceutil.StopService(SERVICE_NAME)
    except Exception:
        pass
    win32serviceutil.RemoveService(SERVICE_NAME)


def install_service() -> None:
    """Install (with auto-start) and start the Windows service (requests elevation via runas)."""
    try:
        import win32serviceutil  # noqa: PLC0415, F401
    except ImportError as exc:
        raise RuntimeError(
            "pywin32 is not installed. Run: pip install pywin32"
        ) from exc
    _run_elevated("_do_install")


def remove_service() -> None:
    """Stop and remove the Windows service (requests elevation via runas)."""
    try:
        import win32serviceutil  # noqa: PLC0415, F401
    except ImportError as exc:
        raise RuntimeError(
            "pywin32 is not installed. Run: pip install pywin32"
        ) from exc
    _run_elevated("_do_remove")


# ---------------------------------------------------------------------------
# Windows Task Scheduler (preferred over Windows Service for wallpaper tasks)
# ---------------------------------------------------------------------------

def install_task_scheduler(interval_minutes: int = 5) -> None:
    """Install a Windows Task Scheduler task that runs at logon and repeats.

    Uses ``schtasks.exe`` so no elevation is required.  The task runs in the
    user's interactive session which is required for wallpaper updates.
    """
    import subprocess  # noqa: PLC0415
    task_name = "MyBGInfoRefresh"
    python_exe = sys.executable
    script = os.path.join(_PROJECT_ROOT, "__main__.py")
    subprocess.run(
        [
            "schtasks", "/Create", "/F",
            "/TN", task_name,
            "/TR", f'"{python_exe}" "{script}"',
            "/SC", "MINUTE",
            "/MO", str(max(1, interval_minutes)),
            "/RL", "HIGHEST",
            "/IT",
        ],
        check=True,
    )


def remove_task_scheduler() -> None:
    """Remove the MyBGInfo Windows Task Scheduler task."""
    import subprocess  # noqa: PLC0415
    subprocess.run(
        ["schtasks", "/Delete", "/F", "/TN", "MyBGInfoRefresh"],
        check=True,
    )


# ---------------------------------------------------------------------------
# Linux autostart (systemd user service with cron fallback)
# ---------------------------------------------------------------------------

def _install_cron(interval_minutes: int, python_exe: str, script: str) -> None:
    """Add a crontab entry for the given interval."""
    import subprocess  # noqa: PLC0415
    cron_line = f"*/{interval_minutes} * * * * {python_exe} {script}\n"
    try:
        existing = subprocess.check_output(
            ["crontab", "-l"], stderr=subprocess.DEVNULL
        ).decode()
    except subprocess.CalledProcessError:
        existing = ""
    if cron_line.strip() not in existing:
        new_cron = existing + cron_line
        proc = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE)
        proc.communicate(new_cron.encode())


def install_linux_autostart(interval_minutes: int = 5) -> None:
    """Install a systemd user service (or cron fallback) for auto-refresh on Linux."""
    import subprocess  # noqa: PLC0415
    if platform.system() != "Linux":
        raise RuntimeError("Not on Linux")

    python_exe = sys.executable
    script = os.path.join(_PROJECT_ROOT, "__main__.py")

    service_content = (
        "[Unit]\n"
        "Description=MyBGInfo Background Refresher\n\n"
        "[Service]\n"
        "Type=simple\n"
        f"ExecStart={python_exe} {script}\n"
        "Restart=always\n"
        f"RestartSec={interval_minutes * 60}\n\n"
        "[Install]\n"
        "WantedBy=default.target\n"
    )
    service_dir = os.path.expanduser("~/.config/systemd/user")
    os.makedirs(service_dir, exist_ok=True)
    service_path = os.path.join(service_dir, "mybginfo.service")
    with open(service_path, "w") as f:
        f.write(service_content)

    try:
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        subprocess.run(
            ["systemctl", "--user", "enable", "--now", "mybginfo.service"], check=True
        )
    except Exception:
        # Fallback: cron
        _install_cron(interval_minutes, python_exe, script)


def remove_linux_autostart() -> None:
    """Remove the systemd user service or cron job for auto-refresh on Linux."""
    import subprocess  # noqa: PLC0415
    # systemd
    try:
        subprocess.run(
            ["systemctl", "--user", "stop", "mybginfo.service"], check=False
        )
        subprocess.run(
            ["systemctl", "--user", "disable", "mybginfo.service"], check=False
        )
        service_path = os.path.expanduser("~/.config/systemd/user/mybginfo.service")
        if os.path.exists(service_path):
            os.remove(service_path)
    except Exception:
        pass
    # cron fallback
    try:
        existing = subprocess.check_output(
            ["crontab", "-l"], stderr=subprocess.DEVNULL
        ).decode()
        new_cron = (
            "\n".join(
                line for line in existing.splitlines() if "__main__.py" not in line
            )
            + "\n"
        )
        proc = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE)
        proc.communicate(new_cron.encode())
    except Exception:
        pass


# ---------------------------------------------------------------------------
# macOS LaunchAgent
# ---------------------------------------------------------------------------

def install_macos_launchagent(interval_seconds: int = 300) -> None:
    """Install a launchd user agent for auto-refresh on macOS."""
    import plistlib  # noqa: PLC0415
    import subprocess  # noqa: PLC0415

    python_exe = sys.executable
    script = os.path.join(_PROJECT_ROOT, "__main__.py")

    plist = {
        "Label": "com.mybginfo.refresh",
        "ProgramArguments": [python_exe, script],
        "StartInterval": interval_seconds,
        "RunAtLoad": True,
        "StandardOutPath": os.path.expanduser("~/Library/Logs/mybginfo.log"),
        "StandardErrorPath": os.path.expanduser("~/Library/Logs/mybginfo.err"),
    }

    agents_dir = os.path.expanduser("~/Library/LaunchAgents")
    os.makedirs(agents_dir, exist_ok=True)
    plist_path = os.path.join(agents_dir, "com.mybginfo.refresh.plist")

    with open(plist_path, "wb") as f:
        plistlib.dump(plist, f)

    subprocess.run(["launchctl", "load", plist_path], check=True)


def remove_macos_launchagent() -> None:
    """Remove the launchd user agent for auto-refresh on macOS."""
    import subprocess  # noqa: PLC0415

    plist_path = os.path.expanduser(
        "~/Library/LaunchAgents/com.mybginfo.refresh.plist"
    )
    try:
        subprocess.run(["launchctl", "unload", plist_path], check=False)
        if os.path.exists(plist_path):
            os.remove(plist_path)
    except Exception:
        pass


try:
    import win32event
    import win32service
    import win32serviceutil
    import servicemanager

    class MyBGInfoService(win32serviceutil.ServiceFramework):
        """Windows service that periodically refreshes the BGInfo wallpaper."""

        _svc_name_ = SERVICE_NAME
        _svc_display_name_ = SERVICE_DISPLAY

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self._stop_event = win32event.CreateEvent(None, 0, 0, None)

        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self._stop_event)

        def SvcDoRun(self):
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, ""),
            )
            self._run()

        def _run(self):
            # Import here to avoid circular imports at module load time.
            from src.config import load_config  # noqa: PLC0415
            from src.bginfo import generate_wallpaper  # noqa: PLC0415
            from src.wallpaper import set_wallpaper  # noqa: PLC0415

            # Always use an absolute config path – when running as a Windows
            # service the CWD is C:\Windows\System32, not the project root.
            cfg_path = os.path.join(_PROJECT_ROOT, "config", "bginfo.json")

            while True:
                cfg = load_config(cfg_path)
                interval = int(cfg.get("refresh_interval", 300))
                try:
                    out = generate_wallpaper(cfg)
                    # Write wallpaper path to registry so it applies even in
                    # Session 0 (services cannot directly update the desktop).
                    try:
                        import winreg  # noqa: PLC0415
                        import ctypes  # noqa: PLC0415
                        key = winreg.OpenKey(
                            winreg.HKEY_CURRENT_USER,
                            r"Control Panel\Desktop",
                            0,
                            winreg.KEY_SET_VALUE,
                        )
                        winreg.SetValueEx(key, "Wallpaper", 0, winreg.REG_SZ, out)
                        winreg.CloseKey(key)
                        # Broadcast the change so it takes effect immediately
                        ctypes.windll.user32.SystemParametersInfoW(0x0014, 0, out, 3)
                    except Exception:
                        pass
                    set_wallpaper(out)
                except Exception as exc:  # pragma: no cover
                    servicemanager.LogErrorMsg(f"MyBGInfoService error: {exc}")

                # Wait for the stop event or for the interval to elapse.
                result = win32event.WaitForSingleObject(
                    self._stop_event, interval * 1000
                )
                if result == win32event.WAIT_OBJECT_0:
                    break  # Stop event signalled

except ImportError:
    pass  # pywin32 not available – service class is not defined


if __name__ == "__main__":
    # Allow module invocation: python -m src.service_manager <action>
    # Supported actions: _do_install, _do_remove, install, remove, start, stop
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action == "_do_install":
        _do_install()
    elif action == "_do_remove":
        _do_remove()
    else:
        try:
            win32serviceutil.HandleCommandLine(MyBGInfoService)
        except NameError:
            print("pywin32 is not installed. Cannot manage the Windows service.")
            sys.exit(1)
