"""Security layer — command and path allowlists for NallyBridge."""

import fnmatch
import re
from pathlib import Path

# ── Command allowlist ──────────────────────────────────────
# Prefixes/patterns that are safe to execute. Checked case-insensitively.
ALLOWED_COMMAND_PREFIXES = [
    # File listing
    "dir",
    "ls",
    "tree",
    "find",
    "where",
    "which",
    # File reading
    "type",
    "cat",
    "head",
    "tail",
    "more",
    "less",
    # File info
    "echo",
    "date",
    "time",
    "whoami",
    "hostname",
    "systeminfo",
    "tasklist",
    "netstat",
    "ipconfig",
    "ifconfig",
    "df",
    "du",
    "wc",
    # Dev tools
    "python",
    "python3",
    "pip",
    "pip3",
    "node",
    "npm",
    "npx",
    "yarn",
    "bun",
    "go",
    "cargo",
    "rustc",
    "java",
    "javac",
    "gcc",
    "g++",
    # Git (read-only)
    "git status",
    "git log",
    "git diff",
    "git show",
    "git branch",
    "git remote",
    "git stash list",
    "git tag",
    # Package managers
    "winget",
    "choco",
    "scoop",
    "apt",
    "brew",
    # Misc safe
    "curl",
    "wget",
    "ping",
    "tracert",
    "nslookup",
]

# ── Command denylist (overrides allowlist) ──────────────────
DENIED_COMMAND_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+~",
    r"rmdir\s+/s\s+/q",
    r"format\s+[a-zA-Z]:",
    r"shutdown",
    r"reboot",
    r"del\s+/[sSfF]\s+\\",
    r"kill\s+-9",
    r"killall",
    r"mkfs\.",
    r"dd\s+if=",
    r"git\s+push\s+--force",
    r"git\s+reset\s+--hard",
    r":(){ :\|:& };:",  # fork bomb
]

# ── Path allowlist ──────────────────────────────────────────
# Only these directories (and their subdirectories) are accessible.
def _get_allowed_dirs() -> list[Path]:
    """Return default allowed directories."""
    home = Path.home()
    dirs = [
        home / "Desktop",
        home / "Documents",
        home / "Downloads",
        home / ".nally",
    ]
    # Add project scan dirs from env if set
    import os
    scan_dirs = os.getenv("NALLY_PROJECT_SCAN_DIRS", "")
    if scan_dirs:
        for d in scan_dirs.split(","):
            d = d.strip()
            if d:
                dirs.append(Path(d))
    return dirs


ALLOWED_PATHS: list[Path] = _get_allowed_dirs()

# Sensitive paths that are always blocked, even if under an allowed dir
BLOCKED_PATH_PATTERNS = [
    "**/.ssh/**",
    "**/.aws/**",
    "**/.gnupg/**",
    "**/id_rsa*",
    "**/id_ed25519*",
    "**/.env",
    "**/credentials.json",
    "**/credentials.json.bak",
]


def is_command_allowed(command: str) -> tuple[bool, str]:
    """Check if a command is allowed. Returns (allowed, reason)."""
    cmd_lower = command.strip().lower()

    # Check denylist first (highest priority)
    for pattern in DENIED_COMMAND_PATTERNS:
        if re.search(pattern, cmd_lower):
            return False, f"Blocked by denylist pattern: {pattern}"

    # Check allowlist — command must start with an allowed prefix
    for prefix in ALLOWED_COMMAND_PREFIXES:
        if cmd_lower.startswith(prefix):
            return True, "allowed"

    return False, f"Command not in allowlist: {cmd_lower.split()[0] if cmd_lower else '(empty)'}"


def is_path_allowed(file_path: str) -> tuple[bool, str]:
    """Check if a file path is allowed. Returns (allowed, reason)."""
    try:
        path = Path(file_path).resolve()
    except Exception:
        return False, f"Invalid path: {file_path}"

    # Check blocked patterns
    path_str = str(path).replace("\\", "/")
    for pattern in BLOCKED_PATH_PATTERNS:
        if fnmatch.fnmatch(path_str, pattern):
            return False, f"Blocked sensitive path: {pattern}"

    # Check allowed directories
    for allowed_dir in ALLOWED_PATHS:
        try:
            allowed_resolved = allowed_dir.resolve()
            if path == allowed_resolved or allowed_resolved in path.parents:
                return True, "allowed"
        except Exception:
            continue

    return False, f"Path not in allowed directories: {path}"
