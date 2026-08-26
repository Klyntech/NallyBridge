# NallyBridge

Lightweight remote execution agent for NALLY. Runs on your local machine, connects to NALLY (cloud or local) via WebSocket, and executes commands on your device.

```
NALLY (Render/cloud) ←→ NallyBridge (your desktop) → local filesystem/commands
```

## Quick Start (Standalone .exe)

### Option A: Build the .exe yourself
```bash
pip install pyinstaller
python build.py
# Output: dist/NallyBridge.exe
```

### Option B: Install from source
```bash
pip install .
nally-bridge --run
```

### First run
1. Copy `NallyBridge.exe` + `.env` to a folder on your machine
2. Double-click `NallyBridge.exe`
3. It auto-installs for auto-start at login
4. Bridge connects to NALLY and stays connected forever

## Configuration (.env)

Place `.env` next to `NallyBridge.exe` (portable) or in `%APPDATA%\NallyBridge\.env` (installed).

| Variable | Required | Description |
|----------|----------|-------------|
| `NALLY_HOST` | Yes | NALLY server address (e.g. `your-app.onrender.com`) |
| `NALLY_BRIDGE_TOKEN` | Yes | Shared secret for bridge auth (must match NALLY's `NALLY_BRIDGE_TOKEN`) |
| `NALLY_USE_SSL` | No | Use `wss://` instead of `ws://` (default: `false`) |
| `NALLY_DEVICE_NAME` | No | Unique device name (default: `desktop`) |
| `NALLY_CMD_TIMEOUT` | No | Command timeout in seconds (default: `60`) |
| `NALLY_LOG_LEVEL` | No | Logging level (default: `INFO`) |

## CLI Commands

```bash
nally-bridge                    # Run the bridge (installs auto-start on first run)
nally-bridge --run              # Run in foreground
nally-bridge --install          # Register auto-start at login
nally-bridge --uninstall        # Remove auto-start
nally-bridge --status           # Show config
nally-bridge --test             # Test local execution
nally-bridge --version          # Show version
```

## Building the .exe

```bash
pip install pyinstaller
python build.py
```

Output: `dist/NallyBridge.exe` (single file, ~15-30 MB, no Python required)

## How it works

1. **Double-click** `NallyBridge.exe` (first time only)
2. **Auto-start** registered via Windows Scheduled Task
3. **Every login**: Bridge starts silently, connects to NALLY
4. **NALLY sends commands** → Bridge executes locally → Returns results
5. **Auto-reconnects** if connection drops

## Available Tools

| Tool | Description |
|------|-------------|
| `run_command` | Execute shell commands (PowerShell on Windows) |
| `file_ops` | File operations (write, list, mkdir, delete, move, copy) |
| `read_file` | Read file contents |
| `system_health` | CPU, memory, disk usage |

## Security

- **Command allowlist**: Only whitelisted commands execute (dir, ls, python, git status, etc.)
- **Path allowlist**: Only Desktop, Documents, Downloads, and project dirs are accessible
- **Denylist**: Destructive commands blocked (rm -rf, format, shutdown, etc.)
- **Separate token**: `NALLY_BRIDGE_TOKEN` is separate from NALLY's main access token
- **All executions logged** in NALLY's tool receipts + bridge-side logs

## NALLY Server Setup

Add to NALLY's `.env`:
```
NALLY_BRIDGE_TOKEN=your-bridge-secret-token
```

The bridge WebSocket endpoint is automatically available at:
```
ws://your-nally-host/ws/bridge/{device_id}?token={bridge_token}
```

## Architecture

```
NALLY Server                    NallyBridge
┌──────────────┐    WebSocket    ┌──────────────────┐
│  /ws/bridge  │◄──────────────►│  WebSocket client │
│  BridgeTool  │   Outbound     │  Executor         │
│  Registry    │   from bridge  │  Security layer   │
└──────────────┘                └──────────────────┘
```

- Bridge initiates outbound connection (no port forwarding needed)
- Auto-reconnects with exponential backoff
- Heartbeat ping/pong keeps connection alive
