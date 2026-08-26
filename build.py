"""PyInstaller build script for NallyBridge.

Usage:
    pip install pyinstaller
    python build.py

Output: dist/NallyBridge.exe
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def build():
    """Build NallyBridge.exe with PyInstaller."""
    print("Building NallyBridge.exe...\n")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name", "NallyBridge",
        "--add-data", f"{ROOT / '.env.example'};.",
        "--add-data", f"{ROOT / 'README.md'};.",
        "--hidden-import", "nally_bridge",
        "--hidden-import", "nally_bridge.cli",
        "--hidden-import", "nally_bridge.bridge",
        "--hidden-import", "nally_bridge.config",
        "--hidden-import", "nally_bridge.executor",
        "--hidden-import", "nally_bridge.security",
        "--hidden-import", "nally_bridge.autostart",
        "--hidden-import", "websockets",
        "--hidden-import", "websockets.legacy",
        "--hidden-import", "websockets.legacy.client",
        "--hidden-import", "psutil",
        "--hidden-import", "dotenv",
        "--collect-submodules", "websockets",
        "--distpath", str(ROOT / "dist"),
        "--workpath", str(ROOT / "build"),
        "--specpath", str(ROOT),
        str(ROOT / "nally_bridge" / "__main__.py"),
    ]

    print(f"Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=str(ROOT))

    if result.returncode == 0:
        exe_path = ROOT / "dist" / "NallyBridge.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\nBuild successful!")
            print(f"  Output: {exe_path}")
            print(f"  Size:   {size_mb:.1f} MB")
            print(f"\nTo use:")
            print(f"  1. Copy NallyBridge.exe + .env to target machine")
            print(f"  2. Double-click NallyBridge.exe")
            print(f"  3. Bridge auto-installs and runs at login")
        else:
            print(f"\nBuild completed but exe not found at {exe_path}")
    else:
        print(f"\nBuild failed with exit code {result.returncode}")
        sys.exit(1)


if __name__ == "__main__":
    build()
