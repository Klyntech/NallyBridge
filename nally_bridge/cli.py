"""NallyBridge CLI — clean entry point for the application."""

import argparse
import asyncio
import logging
import sys


def _setup_logging(level_name: str = "INFO"):
    """Configure logging for the bridge."""
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("websockets").setLevel(logging.WARNING)


def _print_status():
    """Print bridge config status."""
    from . import __version__
    from .config import DEVICE_NAME, NALLY_BRIDGE_TOKEN, NALLY_HOST, NALLY_USE_SSL

    print(f"NallyBridge v{__version__}")
    print(f"  Device:  {DEVICE_NAME}")
    print(f"  Target:  {NALLY_HOST}")
    print(f"  SSL:     {NALLY_USE_SSL}")
    print(f"  Token:   {'set' if NALLY_BRIDGE_TOKEN else 'NOT SET'}")
    print()


def _run_bridge():
    """Run the bridge in foreground."""
    from .config import validate

    errors = validate()
    if errors:
        print("Configuration errors:")
        for e in errors:
            print(f"  - {e}")
        print("\nSet values in .env or environment variables.")
        sys.exit(1)

    _print_status()
    logging.getLogger("nally_bridge").info("Starting NallyBridge...")

    from .bridge import NallyBridge

    bridge = NallyBridge()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(bridge.start())
    except KeyboardInterrupt:
        logging.getLogger("nally_bridge").info("Interrupted — shutting down")
        loop.run_until_complete(bridge.stop())
    finally:
        loop.close()


def _run_test():
    """Test local tool execution."""
    from .executor import execute_tool

    print("Testing NallyBridge local execution...\n")

    tests = [
        ("system_health", {}),
        ("run_command", {"command": "echo hello from NallyBridge"}),
        ("file_ops", {"action": "list", "file_path": str(__import__("pathlib").Path.home() / "Desktop")}),
    ]

    for tool, args in tests:
        print(f">>> {tool}({args})")
        result, success = execute_tool(tool, args)
        status = "OK" if success else "ERROR"
        print(f"[{status}] {result[:200]}")
        print()


def _install_service():
    """Install NallyBridge as an auto-start scheduled task."""
    from .autostart import install, is_installed

    if is_installed():
        print("NallyBridge is already installed for auto-start.")
        print("Use 'nally-bridge --uninstall' to remove first.")
        return

    success = install()
    if success:
        print("NallyBridge installed for auto-start at login.")
        print("It will start automatically next time you log in.")
        print("Use 'nally-bridge --run' to start it now.")
    else:
        print("Failed to install auto-start task.")
        print("Try running as administrator, or use NSSM manually.")


def _uninstall_service():
    """Remove NallyBridge auto-start scheduled task."""
    from .autostart import is_installed, uninstall

    if not is_installed():
        print("NallyBridge is not installed for auto-start.")
        return

    success = uninstall()
    if success:
        print("NallyBridge auto-start removed.")
    else:
        print("Failed to remove auto-start task.")
        print("Try running as administrator.")


def main():
    parser = argparse.ArgumentParser(
        prog="nally-bridge",
        description="NallyBridge — remote execution agent for NALLY",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__import__('nally_bridge').__version__}")
    parser.add_argument("--run", action="store_true", help="Run the bridge in foreground")
    parser.add_argument("--install", action="store_true", help="Install auto-start at login")
    parser.add_argument("--uninstall", action="store_true", help="Remove auto-start at login")
    parser.add_argument("--status", action="store_true", help="Show bridge config")
    parser.add_argument("--test", action="store_true", help="Test local execution")
    parser.add_argument("--log-level", default="INFO", help="Log level (default: INFO)")

    args = parser.parse_args()
    _setup_logging(args.log_level)

    if args.status:
        _print_status()
        return

    if args.test:
        _run_test()
        return

    if args.install:
        _install_service()
        return

    if args.uninstall:
        _uninstall_service()
        return

    # Default: run the bridge (or install on first run)
    from .autostart import is_installed

    if not is_installed():
        print("First run detected. Installing auto-start...")
        from .autostart import install
        install()
        print()

    _run_bridge()


if __name__ == "__main__":
    main()
