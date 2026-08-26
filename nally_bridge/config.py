"""NallyBridge configuration — reads from environment variables or .env file.

Config resolution order:
  1. .env next to the executable (portable mode)
  2. %APPDATA%/NallyBridge/.env (installed mode)
  3. .env next to this file (dev mode)
  4. Environment variables
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def _find_env_file() -> Path | None:
    """Find the .env file in priority order."""
    candidates = []

    if getattr(sys, "frozen", False):
        # Running as PyInstaller .exe
        exe_dir = Path(sys.executable).parent
        candidates.append(exe_dir / ".env")
        # %APPDATA%/NallyBridge/.env
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            candidates.append(Path(appdata) / "NallyBridge" / ".env")
    else:
        # Running as Python — check project root first
        project_root = Path(__file__).parent.parent
        candidates.append(project_root / ".env")

    for p in candidates:
        if p.exists():
            return p

    return None


_env_file = _find_env_file()
if _env_file:
    load_dotenv(_env_file, override=True)

# NALLY server connection
NALLY_HOST = os.getenv("NALLY_HOST", "localhost:5000")
NALLY_BRIDGE_TOKEN = os.getenv("NALLY_BRIDGE_TOKEN", "")
NALLY_USE_SSL = os.getenv("NALLY_USE_SSL", "false").lower() == "true"

# Device identity
DEVICE_NAME = os.getenv("NALLY_DEVICE_NAME", "desktop")
DEVICE_PLATFORM = os.getenv("NALLY_DEVICE_PLATFORM", "")  # auto-detect if empty

# Execution limits
CMD_TIMEOUT = int(os.getenv("NALLY_CMD_TIMEOUT", "60"))
FILE_READ_MAX = int(os.getenv("NALLY_FILE_READ_MAX", "1048576"))  # 1MB

# Reconnection
RECONNECT_BASE_DELAY = float(os.getenv("NALLY_RECONNECT_BASE", "2"))
RECONNECT_MAX_DELAY = float(os.getenv("NALLY_RECONNECT_MAX", "60"))
PING_INTERVAL = int(os.getenv("NALLY_PING_INTERVAL", "30"))

# Logging
LOG_LEVEL = os.getenv("NALLY_LOG_LEVEL", "INFO")


def detect_platform() -> str:
    """Auto-detect the platform if not explicitly set."""
    if DEVICE_PLATFORM:
        return DEVICE_PLATFORM
    import platform
    return platform.system().lower()


def validate() -> list[str]:
    """Return list of config errors (empty = valid)."""
    errors = []
    if not NALLY_HOST:
        errors.append("NALLY_HOST is required")
    if not NALLY_BRIDGE_TOKEN:
        errors.append("NALLY_BRIDGE_TOKEN is required")
    if CMD_TIMEOUT < 5 or CMD_TIMEOUT > 300:
        errors.append("NALLY_CMD_TIMEOUT must be between 5 and 300")
    return errors
