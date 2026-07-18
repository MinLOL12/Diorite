import asyncio
from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    """
    Manages WebSocket connections per project/channel.
    Channels: builds:{projectId}, logs:{projectId}, files:{projectId}, global
    """
    def __init__(self):
        # channel -> list of websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        async with self._lock:
            if channel not in self.active_connections:
                self.active_connections[channel] = []
            self.active_connections[channel].append(websocket)

    async def disconnect(self, websocket: WebSocket, channel: str):
        async with self._lock:
            if channel in self.active_connections:
                if websocket in self.active_connections[channel]:
                    self.active_connections[channel].remove(websocket)
                if not self.active_connections[channel]:
                    del self.active_connections[channel]

    async def broadcast(self, channel: str, message: dict):
        """Broadcast JSON to all sockets in channel"""
        conns = []
        async with self._lock:
            conns = list(self.active_connections.get(channel, []))
        dead = []
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        # cleanup dead
        if dead:
            async with self._lock:
                for d in dead:
                    if channel in self.active_connections and d in self.active_connections[channel]:
                        self.active_connections[channel].remove(d)

    async def send_to_channel(self, channel: str, message: dict):
        await self.broadcast(channel, message)

    def get_channels(self):
        return list(self.active_connections.keys())

# Singleton
manager = ConnectionManager()
