"""Windows service wrapper for NallyBridge.

Install:
    pip install pywin32
    python service.py install
    python service.py start

Or use NSSM (simpler, no pywin32 needed):
    nssm install NallyBridge "C:\path\to\python.exe" "-m" "nally_bridge"
    nssm start NallyBridge

Uninstall (pywin32):
    python service.py stop
    python service.py remove

Uninstall (NSSM):
    nssm stop NallyBridge
    nssm remove NallyBridge confirm
"""

import asyncio
import logging
import os
import sys
import time

# Add parent dir to path so we can import nally_bridge
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SERVICE_NAME = "NallyBridge"
SERVICE_DISPLAY_NAME = "NallyBridge - NALLY Remote Execution Agent"
SERVICE_DESCRIPTION = "Lightweight agent that connects to NALLY and executes commands on this device."


def setup_logging():
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "nally_bridge.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )


def run_bridge():
    """Run the bridge directly (for testing or non-service usage)."""
    setup_logging()
    logger = logging.getLogger("nally_bridge")

    from nally_bridge.config import validate
    from nally_bridge.bridge import NallyBridge

    errors = validate()
    if errors:
        for e in errors:
            logger.error(f"Config error: {e}")
        return

    bridge = NallyBridge()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(bridge.start())
    except KeyboardInterrupt:
        logger.info("Interrupted")
        loop.run_until_complete(bridge.stop())
    finally:
        loop.close()


try:
    import win32event
    import win32service
    import win32serviceutil
    import servicemanager

    class NallyBridgeService(win32serviceutil.ServiceFramework):
        """Windows service for NallyBridge."""

        _svc_name_ = SERVICE_NAME
        _svc_display_name_ = SERVICE_DISPLAY_NAME
        _svc_description_ = SERVICE_DESCRIPTION

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.stop_event = win32event.CreateEvent(None, 0, 0, None)
            self.bridge = None
            self.loop = None

        def SvcStop(self):
            """Called by Windows to stop the service."""
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.stop_event)
            if self.bridge:
                asyncio.run_coroutine_threadsafe(self.bridge.stop(), self.loop)

        def SvcDoRun(self):
            """Called by Windows to start the service."""
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, ""),
            )
            self._run()

        def _run(self):
            setup_logging()
            logger = logging.getLogger("nally_bridge")

            from nally_bridge.config import validate
            from nally_bridge.bridge import NallyBridge

            errors = validate()
            if errors:
                for e in errors:
                    logger.error(f"Config error: {e}")
                return

            self.bridge = NallyBridge()
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            # Run bridge in background, wait on stop event
            bridge_task = self.loop.create_task(self.bridge.start())

            # Block until stop event
            win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)

            # Cleanup
            self.loop.run_until_complete(self.bridge.stop())
            self.loop.close()

    if __name__ == "__main__":
        if len(sys.argv) == 1:
            # Running as a service
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(NallyBridgeService)
            servicemanager.StartServiceCtrlDispatcher()
        else:
            # Command-line mode (install, remove, start, stop)
            win32serviceutil.HandleCommandLine(NallyBridgeService)

except ImportError:
    # pywin32 not installed — fall back to direct execution
    if __name__ == "__main__":
        if len(sys.argv) > 1 and sys.argv[1] in ("install", "remove", "start", "stop"):
            print("pywin32 is required for Windows service mode.")
            print("Install: pip install pywin32")
            print("Or use NSSM: https://nssm.cc/")
            print()
            print("Running in direct mode instead...")
            print()

        run_bridge()
