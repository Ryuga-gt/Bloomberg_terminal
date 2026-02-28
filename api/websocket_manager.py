"""
api.websocket_manager
======================

WebSocket connection manager for real-time equity curve streaming.

Supports multiple simultaneous subscribers.  Each connected client
receives equity updates broadcast by the server.

Usage
-----
    manager = WebSocketManager()

    # In a FastAPI WebSocket endpoint:
    await manager.connect(websocket)
    try:
        while True:
            await manager.broadcast({"equity": 12345.67})
            await asyncio.sleep(1)
    finally:
        manager.disconnect(websocket)
"""

import asyncio
import json
from typing import List

from fastapi import WebSocket


class WebSocketManager:
    """
    Manages active WebSocket connections and broadcasts messages.

    Thread-safety: designed for use within a single asyncio event loop.
    """

    def __init__(self) -> None:
        self._active_connections: List[WebSocket] = []

    # ------------------------------------------------------------------

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self._active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if websocket in self._active_connections:
            self._active_connections.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        """
        Send *message* (as JSON) to all active connections.

        Connections that fail to receive are silently removed.
        """
        dead = []
        for connection in list(self._active_connections):
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                dead.append(connection)
        for conn in dead:
            self.disconnect(conn)

    async def send_personal(self, websocket: WebSocket, message: dict) -> None:
        """Send *message* to a single connection."""
        await websocket.send_text(json.dumps(message))

    @property
    def connection_count(self) -> int:
        """Number of active connections."""
        return len(self._active_connections)
