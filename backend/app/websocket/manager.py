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

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a disconnected WebSocket."""
        self.active_connections.discard(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        message["timestamp"] = datetime.utcnow().isoformat()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")

    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send message to specific client."""
        message["timestamp"] = datetime.utcnow().isoformat()
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await manager.send_personal(websocket, {"type": "pong"})
            elif message.get("type") == "subscribe":
                # Handle channel subscription
                channel = message.get("channel")
                logger.info(f"Client subscribed to channel: {channel}")
                await manager.send_personal(
                    websocket,
                    {"type": "subscribed", "channel": channel}
                )
            elif message.get("type") == "unsubscribe":
                # Handle channel unsubscription
                channel = message.get("channel")
                logger.info(f"Client unsubscribed from channel: {channel}")
                await manager.send_personal(
                    websocket,
                    {"type": "unsubscribed", "channel": channel}
                )
            else:
                logger.warning(f"Unknown message type: {message.get('type')}")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
