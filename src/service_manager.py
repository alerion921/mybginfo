"""Windows service manager for MyBGInfo.

Requires pywin32 (``pip install pywin32``).  This module is a no-op on
non-Windows platforms; the service class is only defined when pywin32 is
available.
"""
import os
import platform
import sys
import tempfile
import time
from xml.sax.saxutils import escape as _xml_escape

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
    """Install a Windows Task Scheduler task that repeats at the given interval.

    Uses an XML task definition imported via ``schtasks /Create /XML`` to avoid
    command-line quoting issues with the ``/TR`` flag.  The task runs in the
    user's interactive session (required for wallpaper updates) and does **not**
    require elevation.
    """
    import subprocess  # noqa: PLC0415

    task_name = "MyBGInfoRefresh"
    python_exe = sys.executable
    script = os.path.join(_PROJECT_ROOT, "__main__.py")

    # XML task definition – avoids /TR double-quoting problems entirely.
    xml_content = (
        '<?xml version="1.0" encoding="UTF-16"?>\n'
        '<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">\n'
        "  <Triggers>\n"
        "    <TimeTrigger>\n"
        "      <Repetition>\n"
        f"        <Interval>PT{interval_minutes}M</Interval>\n"
        "        <StopAtDurationEnd>false</StopAtDurationEnd>\n"
        "      </Repetition>\n"
        "      <StartBoundary>2000-01-01T00:00:00</StartBoundary>\n"
        "      <Enabled>true</Enabled>\n"
        "    </TimeTrigger>\n"
        "  </Triggers>\n"
        "  <Principals>\n"
        '    <Principal id="Author">\n'
        "      <LogonType>InteractiveToken</LogonType>\n"
        "      <RunLevel>LeastPrivilege</RunLevel>\n"
        "    </Principal>\n"
        "  </Principals>\n"
        '  <Actions Context="Author">\n'
        "    <Exec>\n"
        f"      <Command>{_xml_escape(python_exe)}</Command>\n"
        f'      <Arguments>"{_xml_escape(script)}"</Arguments>\n'
        f"      <WorkingDirectory>{_xml_escape(_PROJECT_ROOT)}</WorkingDirectory>\n"
        "    </Exec>\n"
        "  </Actions>\n"
        "  <Settings>\n"
        "    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>\n"
        "    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>\n"
        "    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>\n"
        "    <AllowHardTerminate>true</AllowHardTerminate>\n"
        "    <StartWhenAvailable>true</StartWhenAvailable>\n"
        "    <AllowStartOnDemand>true</AllowStartOnDemand>\n"
        "    <Enabled>true</Enabled>\n"
        "    <Hidden>false</Hidden>\n"
        "    <RunOnlyIfIdle>false</RunOnlyIfIdle>\n"
        "    <WakeToRun>false</WakeToRun>\n"
        "    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>\n"
        "    <Priority>7</Priority>\n"
        "  </Settings>\n"
        "</Task>\n"
    )

    fd, xml_path = tempfile.mkstemp(suffix=".xml")
    try:
        with os.fdopen(fd, "w", encoding="utf-16") as fh:
            fh.write(xml_content)
        subprocess.run(
            ["schtasks", "/Create", "/F", "/TN", task_name, "/XML", xml_path],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode(errors="replace") if exc.stderr else ""
        raise RuntimeError(
            f"Failed to create scheduled task: {stderr.strip()}"
        ) from exc
    finally:
        try:
            os.unlink(xml_path)
        except OSError:
            pass


def remove_task_scheduler() -> None:
    """Remove the MyBGInfo Windows Task Scheduler task.

    Succeeds silently when the task does not exist so that the user is not
    shown a confusing error after an already-deleted (or never-created) task.
    """
    import subprocess  # noqa: PLC0415

    result = subprocess.run(
        ["schtasks", "/Delete", "/F", "/TN", "MyBGInfoRefresh"],
        capture_output=True,
    )
    if result.returncode != 0:
        stderr = (result.stderr.decode(errors="replace") if result.stderr else "").lower()
        # Tolerate "does not exist" / "cannot find" – the task is already gone.
        if "does not exist" not in stderr and "cannot find" not in stderr:
            raise RuntimeError(
                f"Failed to remove scheduled task: "
                f"{result.stderr.decode(errors='replace').strip() if result.stderr else 'unknown error'}"
            )


# ---------------------------------------------------------------------------
# Task / autostart status query (cross-platform)
# ---------------------------------------------------------------------------

def _query_windows_task() -> str:
    """Return the status of the MyBGInfoRefresh scheduled task on Windows."""
    import subprocess  # noqa: PLC0415
    try:
        result = subprocess.run(
            ["schtasks", "/Query", "/TN", "MyBGInfoRefresh"],
            capture_output=True,
        )
        return "Installed" if result.returncode == 0 else "Not installed"
    except Exception:
        return "Unknown"


def _query_linux_autostart() -> str:
    """Return the status of the mybginfo autostart on Linux."""
    import subprocess  # noqa: PLC0415

    service_path = os.path.expanduser("~/.config/systemd/user/mybginfo.service")
    if os.path.exists(service_path):
        try:
            result = subprocess.run(
                ["systemctl", "--user", "is-active", "mybginfo.service"],
                capture_output=True,
            )
            if result.returncode == 0:
                return "Installed (active)"
            return "Installed (inactive)"
        except Exception:
            return "Installed"

    # Fallback: check cron
    try:
        existing = subprocess.check_output(
            ["crontab", "-l"], stderr=subprocess.DEVNULL
        ).decode()
        if "__main__.py" in existing:
            return "Installed (cron)"
    except Exception:
        pass

    return "Not installed"


def _query_macos_launchagent() -> str:
    """Return the status of the mybginfo LaunchAgent on macOS."""
    plist_path = os.path.expanduser(
        "~/Library/LaunchAgents/com.mybginfo.refresh.plist"
    )
    return "Installed" if os.path.exists(plist_path) else "Not installed"


def get_task_status() -> str:
    """Return a human-readable status string for the platform autostart mechanism."""
    system = platform.system()
    if system == "Windows":
        return _query_windows_task()
    if system == "Linux":
        return _query_linux_autostart()
    if system == "Darwin":
        return _query_macos_launchagent()
    return "Unsupported platform"


def create_desktop_shortcut() -> None:
    """Create a desktop shortcut to the application (Windows only, idempotent).

    Uses ``pywin32``'s ``win32com.client`` to create a ``.lnk`` file on the
    user's Desktop.  Fails silently if ``pywin32`` is not available.
    """
    shortcut_path = os.path.join(
        os.environ.get("USERPROFILE", os.path.expanduser("~")),
        "Desktop",
        "MyBGInfo.lnk",
    )
    if os.path.exists(shortcut_path):
        return
    try:
        import win32com.client  # noqa: PLC0415
    except ImportError:
        return
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(shortcut_path)
    if getattr(sys, "frozen", False):
        # Running as a frozen executable – no separate script needed.
        shortcut.TargetPath = sys.executable
        shortcut.Arguments = ""
    else:
        shortcut.TargetPath = sys.executable
        shortcut.Arguments = f'"{os.path.join(_PROJECT_ROOT, "__main__.py")}"'
    shortcut.WorkingDirectory = _PROJECT_ROOT
    shortcut.IconLocation = sys.executable
    shortcut.Save()


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
