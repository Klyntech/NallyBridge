"""Local command executor — runs the 4 core tools on the bridge device."""

import os
import platform
import subprocess
import time
from pathlib import Path

from .config import CMD_TIMEOUT, FILE_READ_MAX
from .security import is_command_allowed, is_path_allowed


def run_command(command: str, timeout: int | None = None) -> str:
    """Execute a shell command locally. Returns output string."""
    allowed, reason = is_command_allowed(command)
    if not allowed:
        return f"Error: Command blocked — {reason}"

    timeout = timeout or CMD_TIMEOUT
    is_windows = platform.system() == "Windows"

    # Normalize multi-statement commands for PowerShell
    if is_windows and "&&" in command:
        parts = [p.strip() for p in command.split("&&") if p.strip()]
        command = "; ".join(parts)

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(Path.home()),
        )

        output_parts = []
        if result.stdout:
            output_parts.append(result.stdout.strip())
        if result.stderr:
            output_parts.append(f"[stderr]\n{result.stderr.strip()}")

        output = "\n".join(output_parts) if output_parts else "(no output)"

        # Truncate if too long
        if len(output) > 50000:
            output = output[:50000] + "\n... (truncated)"

        if result.returncode != 0:
            return f"[exit code {result.returncode}]\n{output}"

        return output

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout}s"
    except Exception as e:
        return f"Error executing command: {type(e).__name__}: {e}"


def file_ops(action: str, file_path: str, content: str = "", destination: str = "") -> str:
    """File operations: write, list, mkdir, delete, move, copy."""
    allowed, reason = is_path_allowed(file_path)
    if not allowed:
        return f"Error: Path blocked — {reason}"

    if destination:
        dest_allowed, dest_reason = is_path_allowed(destination)
        if not dest_allowed:
            return f"Error: Destination blocked — {dest_reason}"

    path = Path(file_path)

    try:
        if action == "write":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return f"Wrote {len(content)} chars to {file_path}"

        elif action == "list":
            if not path.exists():
                return f"Error: Directory not found: {file_path}"
            if not path.is_dir():
                return f"Error: Not a directory: {file_path}"

            entries = []
            for entry in sorted(path.iterdir()):
                if entry.is_dir():
                    size = sum(f.stat().st_size for f in entry.rglob("*") if f.is_file())
                    entries.append(f"[dir] {entry.name} ({_format_size(size)})")
                else:
                    entries.append(f"      {entry.name} ({_format_size(entry.stat().st_size)})")
            return "\n".join(entries) if entries else "(empty directory)"

        elif action == "mkdir":
            path.mkdir(parents=True, exist_ok=True)
            return f"Created directory: {file_path}"

        elif action == "delete":
            if not path.exists():
                return f"Error: Not found: {file_path}"
            if path.is_dir():
                import shutil
                shutil.rmtree(path)
                return f"Deleted directory: {file_path}"
            else:
                path.unlink()
                return f"Deleted file: {file_path}"

        elif action == "move":
            dest = Path(destination)
            if dest.exists():
                return f"Error: Destination exists: {destination}"
            path.rename(dest)
            return f"Moved {file_path} -> {destination}"

        elif action == "copy":
            import shutil
            dest = Path(destination)
            if dest.exists():
                return f"Error: Destination exists: {destination}"
            if path.is_dir():
                shutil.copytree(path, dest)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, dest)
            return f"Copied {file_path} -> {destination}"

        else:
            return f"Error: Unknown file_ops action: {action}"

    except Exception as e:
        return f"Error in file_ops ({action}): {type(e).__name__}: {e}"


def read_file(file_path: str) -> str:
    """Read a file's contents."""
    allowed, reason = is_path_allowed(file_path)
    if not allowed:
        return f"Error: Path blocked — {reason}"

    path = Path(file_path)
    if not path.exists():
        return f"Error: File not found: {file_path}"
    if path.is_dir():
        return f"Error: Is a directory, not a file: {file_path}"

    try:
        size = path.stat().st_size
        if size > FILE_READ_MAX:
            return f"Error: File too large ({_format_size(size)}, max {_format_size(FILE_READ_MAX)})"

        content = path.read_text(encoding="utf-8", errors="replace")

        if len(content) > 50000:
            content = content[:50000] + "\n... (truncated at 50K chars)"

        return content

    except Exception as e:
        return f"Error reading file: {type(e).__name__}: {e}"


def system_health() -> str:
    """Return system health info: CPU, memory, disk usage."""
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/" if platform.system() != "Windows" else "C:\\")

        return (
            f"CPU: {cpu}%\n"
            f"Memory: {mem.percent}% ({_format_size(mem.used)} / {_format_size(mem.total)})\n"
            f"Disk: {disk.percent}% ({_format_size(disk.used)} / {_format_size(disk.total)})\n"
            f"Platform: {platform.system()} {platform.release()}\n"
            f"Python: {platform.python_version()}"
        )
    except ImportError:
        # Fallback without psutil
        import platform as pf
        return (
            f"Platform: {pf.system()} {pf.release()}\n"
            f"Python: {pf.python_version()}\n"
            f"Machine: {pf.machine()}\n"
            f"(psutil not installed — CPU/memory/disk stats unavailable)"
        )
    except Exception as e:
        return f"Error getting system health: {e}"


def _format_size(size: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.1f}{unit}" if unit != "B" else f"{size}B"
        size /= 1024
    return f"{size:.1f}PB"


# ── Tool dispatch ──────────────────────────────────────────

TOOL_DISPATCH = {
    "run_command": lambda args: run_command(args.get("command", "")),
    "file_ops": lambda args: file_ops(
        action=args.get("action", ""),
        file_path=args.get("file_path", ""),
        content=args.get("content", ""),
        destination=args.get("destination", ""),
    ),
    "read_file": lambda args: read_file(args.get("file_path", args.get("path", ""))),
    "system_health": lambda args: system_health(),
}


def execute_tool(tool: str, args) -> tuple[str, bool]:
    """Execute a tool by name. Returns (result, success)."""
    # Ensure args is a dict (may arrive as JSON string over WebSocket)
    if isinstance(args, str):
        import json
        try:
            args = json.loads(args)
        except (json.JSONDecodeError, TypeError):
            args = {}
    if not isinstance(args, dict):
        args = {}

    handler = TOOL_DISPATCH.get(tool)
    if not handler:
        return f"Error: Unknown tool: {tool}", False

    try:
        result = handler(args)
        success = not result.startswith("Error:")
        return result, success
    except Exception as e:
        return f"Error executing {tool}: {type(e).__name__}: {e}", False
