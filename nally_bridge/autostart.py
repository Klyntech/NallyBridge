"""Auto-start via Windows Scheduled Task.

Registers NallyBridge to run at user login using schtasks.
No admin privileges required for user-level tasks.
"""

import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("nally_bridge.autostart")

TASK_NAME = "NallyBridge"


def _get_exe_path() -> str:
    """Get the path to the NallyBridge executable."""
    if getattr(sys, "frozen", False):
        # Running as PyInstaller .exe
        return sys.executable
    else:
        # Running as Python — use current interpreter + module
        return f'"{sys.executable}" -m nally_bridge'


def is_installed() -> bool:
    """Check if the auto-start task exists."""
    try:
        result = subprocess.run(
            ["schtasks", "/query", "/tn", TASK_NAME],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def install() -> bool:
    """Create the auto-start scheduled task.

    Runs at user login (onlogon), hidden, with normal priority.
    """
    exe = _get_exe_path()

    # Build schtasks command
    cmd = [
        "schtasks",
        "/create",
        "/tn", TASK_NAME,
        "/tr", exe,
        "/sc", "onlogon",
        "/rl", "limited",
        "/f",  # force overwrite if exists
    ]

    logger.info(f"Installing auto-start task: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
        )

        if result.returncode == 0:
            logger.info("Auto-start task installed successfully")
            return True
        else:
            logger.error(f"schtasks failed: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Failed to install auto-start: {e}")
        return False


def uninstall() -> bool:
    """Remove the auto-start scheduled task."""
    cmd = ["schtasks", "/delete", "/tn", TASK_NAME, "/f"]

    logger.info(f"Removing auto-start task: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            logger.info("Auto-start task removed")
            return True
        else:
            logger.error(f"schtasks failed: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Failed to remove auto-start: {e}")
        return False


def get_status() -> dict:
    """Get info about the auto-start task."""
    installed = is_installed()
    exe = _get_exe_path() if installed else None

    return {
        "installed": installed,
        "task_name": TASK_NAME,
        "exe": exe,
    }
