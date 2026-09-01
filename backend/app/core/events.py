"""Redis Pub/Sub event bus for real-time updates."""

import json
import logging
from typing import Any, Callable, Awaitable, Optional

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

EVENTS_CHANNEL = "channel:events"


class EventPublisher:
    """Publish events to Redis Pub/Sub channel."""

    @staticmethod
    async def publish(topic: str, payload: dict[str, Any]) -> None:
        message = {"topic": topic, "payload": payload}
        redis_client = aioredis.from_url(settings.REDIS_URL)
        try:
            await redis_client.publish(EVENTS_CHANNEL, json.dumps(message))
            logger.debug("Published event: %s", topic)
        except Exception as e:
            logger.error("Failed to publish event %s: %s", topic, e)
        finally:
            await redis_client.aclose()


class EventSubscriber:
    """Subscribe to Redis Pub/Sub and forward events to a handler."""

    def __init__(self, handler: Callable[[dict], Awaitable[None]]):
        self._handler = handler
        self._redis: Optional[aioredis.Redis] = None
        self._pubsub = None
        self._running = False

    async def start(self) -> None:
        self._redis = aioredis.from_url(settings.REDIS_URL)
        self._pubsub = self._redis.pubsub()
        await self._pubsub.subscribe(EVENTS_CHANNEL)
        self._running = True
        logger.info("Redis event subscriber started on %s", EVENTS_CHANNEL)

        async for message in self._pubsub.listen():
            if not self._running:
                break
            if message["type"] != "message":
                continue
            try:
                data = json.loads(message["data"])
                await self._handler(data)
            except Exception as e:
                logger.error("Error handling Redis event: %s", e)

    async def stop(self) -> None:
        self._running = False
        if self._pubsub:
            await self._pubsub.unsubscribe(EVENTS_CHANNEL)
            await self._pubsub.aclose()
        if self._redis:
            await self._redis.aclose()
        logger.info("Redis event subscriber stopped")
