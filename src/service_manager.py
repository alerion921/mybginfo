"""Windows service manager for MyBGInfo.

Requires pywin32 (``pip install pywin32``).  This module is a no-op on
non-Windows platforms; the service class is only defined when pywin32 is
available.
"""
import os
import sys
import time

SERVICE_NAME = "MyBGInfoService"
SERVICE_DISPLAY = "MyBGInfo Background Refresher"

# Path to this script – used when registering the service.
_SCRIPT = os.path.abspath(__file__)


def install_service() -> None:
    """Install and start the Windows service (requests elevation via runas)."""
    import ctypes  # noqa: PLC0415
    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        f'"{_SCRIPT}" install',
        None,
        1,
    )


def remove_service() -> None:
    """Stop and remove the Windows service (requests elevation via runas)."""
    import ctypes  # noqa: PLC0415
    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        f'"{_SCRIPT}" remove',
        None,
        1,
    )


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

            while True:
                cfg = load_config()
                interval = int(cfg.get("refresh_interval", 300))
                try:
                    out = generate_wallpaper(cfg)
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
    # Allow direct invocation: python service_manager.py install|remove|start|stop
    try:
        win32serviceutil.HandleCommandLine(MyBGInfoService)
    except NameError:
        print("pywin32 is not installed. Cannot manage the Windows service.")
        sys.exit(1)
