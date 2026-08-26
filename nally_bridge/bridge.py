"""WebSocket client — connects NallyBridge to NALLY server."""

import asyncio
import json
import logging
import platform
import time

from .config import (
    DEVICE_NAME,
    NALLY_BRIDGE_TOKEN,
    NALLY_HOST,
    NALLY_USE_SSL,
    PING_INTERVAL,
    RECONNECT_BASE_DELAY,
    RECONNECT_MAX_DELAY,
)
from .executor import execute_tool

logger = logging.getLogger("nally_bridge")

# Available tools this bridge exposes
BRIDGE_TOOLS = ["run_command", "file_ops", "read_file", "system_health"]


class NallyBridge:
    """WebSocket client that connects to NALLY and executes remote commands."""

    def __init__(self):
        self.ws = None
        self.connected = False
        self.running = False
        self._reconnect_delay = RECONNECT_BASE_DELAY
        self._last_pong = 0.0

    @property
    def _ws_url(self) -> str:
        protocol = "wss" if NALLY_USE_SSL else "ws"
        host = NALLY_HOST.rstrip("/")
        return f"{protocol}://{host}/ws/bridge/{DEVICE_NAME}?token={NALLY_BRIDGE_TOKEN}"

    async def start(self):
        """Start the bridge client with auto-reconnect."""
        self.running = True
        logger.info(f"NallyBridge starting — device: {DEVICE_NAME}, target: {NALLY_HOST}")

        while self.running:
            try:
                await self._connect_and_listen()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Connection error: {e}")

            if not self.running:
                break

            # Exponential backoff reconnect
            logger.info(f"Reconnecting in {self._reconnect_delay:.1f}s...")
            await asyncio.sleep(self._reconnect_delay)
            self._reconnect_delay = min(
                self._reconnect_delay * 2, RECONNECT_MAX_DELAY
            )

    async def stop(self):
        """Stop the bridge client."""
        self.running = False
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
        logger.info("NallyBridge stopped")

    async def _connect_and_listen(self):
        """Connect to NALLY WebSocket and process messages."""
        try:
            import websockets
        except ImportError:
            logger.error("websockets package not installed. Run: pip install websockets")
            return

        logger.info(f"Connecting to {self._ws_url}")

        async with websockets.connect(
            self._ws_url,
            ping_interval=PING_INTERVAL,
            ping_timeout=10,
            max_size=10 * 1024 * 1024,  # 10MB max message
        ) as ws:
            self.ws = ws
            self.connected = True
            self._reconnect_delay = RECONNECT_BASE_DELAY
            logger.info("Connected to NALLY")

            # Register this bridge
            await self._send({
                "type": "bridge_register",
                "device": DEVICE_NAME,
                "platform": platform.system().lower(),
                "tools": BRIDGE_TOOLS,
                "version": "0.1.0",
            })

            # Listen for messages
            async for raw_msg in ws:
                try:
                    msg = json.loads(raw_msg)
                    await self._handle_message(msg)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {raw_msg[:100]}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")

    async def _handle_message(self, msg: dict):
        """Handle a message from NALLY."""
        msg_type = msg.get("type", "")

        if msg_type == "tool_request":
            await self._handle_tool_request(msg)

        elif msg_type == "ping":
            self._last_pong = time.time()
            await self._send({"type": "pong"})

        elif msg_type == "pong":
            self._last_pong = time.time()

        elif msg_type == "registered":
            logger.info(f"Registered as bridge: {msg.get('session_id', DEVICE_NAME)}")

        elif msg_type == "error":
            logger.warning(f"Server error: {msg.get('text', 'unknown')}")

        else:
            logger.debug(f"Unknown message type: {msg_type}")

    async def _handle_tool_request(self, msg: dict):
        """Execute a tool request and send the result back."""
        request_id = msg.get("request_id", "")
        tool = msg.get("tool", "")
        args = msg.get("args", {})

        logger.info(f"Tool request: {tool} (id={request_id})")

        # Execute in thread pool to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        result, success = await loop.run_in_executor(None, execute_tool, tool, args)

        logger.info(f"Tool result: {tool} -> {'OK' if success else 'ERROR'} ({len(result)} chars)")

        await self._send({
            "type": "tool_result",
            "request_id": request_id,
            "result": result,
            "success": success,
        })

    async def _send(self, msg: dict):
        """Send a JSON message to NALLY."""
        if self.ws and self.connected:
            try:
                await self.ws.send(json.dumps(msg))
            except Exception as e:
                logger.error(f"Send error: {e}")
                self.connected = False
