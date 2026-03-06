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
