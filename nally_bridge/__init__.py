"""NallyBridge — Lightweight remote execution agent for NALLY."""

__version__ = "0.1.0"
__author__ = "Clinton (Klyntech)"

from .bridge import NallyBridge
from .config import DEVICE_NAME, NALLY_HOST

__all__ = ["NallyBridge", "DEVICE_NAME", "NALLY_HOST", "__version__"]
