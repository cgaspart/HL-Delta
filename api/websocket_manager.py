import asyncio
import logging
from typing import List
from fastapi import WebSocket

class ConnectionManager:
    """Manages active WebSocket connections for broadcasting messages."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket."""
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        """Broadcast a message to all active connections."""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                # The connection might have closed, remove it.
                self.disconnect(connection)

# Create a single instance of the manager to be used across the application
manager = ConnectionManager()

class WebSocketLogHandler(logging.Handler):
    """A custom logging handler that broadcasts log records to WebSockets."""
    def __init__(self, manager_instance: ConnectionManager):
        super().__init__()
        self.manager = manager_instance

    def emit(self, record):
        """Emit a log record."""
        try:
            msg = self.format(record)
            # Use asyncio.create_task to send the message without blocking the logger
            asyncio.create_task(self.manager.broadcast(msg))
        except Exception:
            self.handleError(record)
