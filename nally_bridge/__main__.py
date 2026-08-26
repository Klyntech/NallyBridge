"""NallyBridge entry point — run with `python -m nally_bridge` or as .exe."""

import sys

if __name__ == "__main__" or getattr(sys, "frozen", False):
    # When running as .exe or via __main__, import and call main
    from nally_bridge.cli import main
    main()
