import asyncio
import logging
from fastapi import WebSocket, WebSocketDisconnect
from typing import Set
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._subscriptions: dict[WebSocket, set[str]] = {}

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        self._subscriptions[websocket] = set()
        logger.info("Client connected. Total connections: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        """Remove a disconnected WebSocket."""
        self.active_connections.discard(websocket)
        self._subscriptions.pop(websocket, None)
        logger.info("Client disconnected. Total connections: %d", len(self.active_connections))

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        message["timestamp"] = datetime.utcnow().isoformat()
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error("Error broadcasting to client: %s", e)

    async def broadcast_event(self, event: dict):
        """Broadcast Redis event to subscribed clients."""
        topic = event.get("topic", "")
        payload = event.get("payload", {})
        message = {
            "type": "event",
            "topic": topic,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
        }

        for connection in list(self.active_connections):
            subs = self._subscriptions.get(connection, set())
            if subs and topic not in subs and "*" not in subs:
                continue
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error("Error sending event to client: %s", e)

    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send message to specific client."""
        message["timestamp"] = datetime.utcnow().isoformat()
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error("Error sending personal message: %s", e)

    def subscribe(self, websocket: WebSocket, channel: str):
        """Subscribe client to a channel/topic."""
        if websocket in self._subscriptions:
            self._subscriptions[websocket].add(channel)

    def unsubscribe(self, websocket: WebSocket, channel: str):
        """Unsubscribe client from a channel/topic."""
        if websocket in self._subscriptions:
            self._subscriptions[websocket].discard(channel)


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "ping":
                await manager.send_personal(websocket, {"type": "pong"})
            elif message.get("type") == "subscribe":
                channel = message.get("channel", "*")
                manager.subscribe(websocket, channel)
                logger.info("Client subscribed to channel: %s", channel)
                await manager.send_personal(
                    websocket,
                    {"type": "subscribed", "channel": channel},
                )
            elif message.get("type") == "unsubscribe":
                channel = message.get("channel")
                if channel:
                    manager.unsubscribe(websocket, channel)
                logger.info("Client unsubscribed from channel: %s", channel)
                await manager.send_personal(
                    websocket,
                    {"type": "unsubscribed", "channel": channel},
                )
            else:
                logger.warning("Unknown message type: %s", message.get("type"))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error("WebSocket error: %s", e)
        manager.disconnect(websocket)
