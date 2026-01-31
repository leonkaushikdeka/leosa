import json
import logging
from typing import Optional, Any
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio import Redis

from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

redis_client: Optional[Redis] = None


async def init_redis():
    global redis_client
    try:
        redis_client = redis.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            db=settings.redis.db,
            password=settings.redis.password or None,
            decode_responses=settings.redis.decode_responses,
        )
        await redis_client.ping()
        logger.info("Redis initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        raise


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")


async def get_redis() -> Redis:
    if redis_client is None:
        await init_redis()
    return redis_client


class RedisCache:
    def __init__(self):
        self.prefix = "ransomware:"

    async def get(self, key: str) -> Optional[Any]:
        client = await get_redis()
        value = await client.get(f"{self.prefix}{key}")
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def set(self, key: str, value: Any, expire_seconds: int = 3600) -> None:
        client = await get_redis()
        serialized = json.dumps(value) if not isinstance(value, str) else value
        await client.setex(f"{self.prefix}{key}", expire_seconds, serialized)

    async def delete(self, key: str) -> None:
        client = await get_redis()
        await client.delete(f"{self.prefix}{key}")

    async def incr(self, key: str) -> int:
        client = await get_redis()
        return await client.incr(f"{self.prefix}{key}")

    async def setnx(self, key: str, value: Any) -> bool:
        client = await get_redis()
        serialized = json.dumps(value) if not isinstance(value, str) else value
        return await client.setnx(f"{self.prefix}{key}, serialized")

    async def add_to_set(self, key: str, *values: Any) -> int:
        client = await get_redis()
        for value in values:
            serialized = json.dumps(value) if not isinstance(value, str) else value
            await client.sadd(f"{self.prefix}{key}", serialized)

    async def get_set_members(self, key: str) -> set:
        client = await get_redis()
        members = await client.smembers(f"{self.prefix}{key}")
        result = set()
        for member in members:
            try:
                result.add(json.loads(member))
            except json.JSONDecodeError:
                result.add(member)
        return result

    async def publish(self, channel: str, message: Any) -> int:
        client = await get_redis()
        serialized = json.dumps(message) if not isinstance(message, str) else message
        return await client.publish(f"{self.prefix}{channel}", serialized)


cache = RedisCache()
