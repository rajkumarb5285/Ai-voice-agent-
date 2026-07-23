import redis.asyncio as aioredis
from app.config import settings
from app.utils.logger import logger

redis_client = None


class MockRedis:
    """In-memory Redis fallback for environments without a running Redis server."""

    def __init__(self):
        self.store = {}
        logger.info("redis_mock_initialized", message="Using in-memory Redis fallback")

    async def ping(self):
        return True

    async def rpush(self, key, value):
        if key not in self.store:
            self.store[key] = []
        self.store[key].append(value)
        return len(self.store[key])

    async def ltrim(self, key, start, end):
        if key in self.store:
            lst = self.store[key]
            length = len(lst)
            s = start if start >= 0 else max(0, length + start)
            e = end if end >= 0 else max(0, length + end)
            self.store[key] = lst[s:e+1]
        return True

    async def lrange(self, key, start, end):
        if key not in self.store:
            return []
        lst = self.store[key]
        length = len(lst)
        s = start if start >= 0 else max(0, length + start)
        e = end if end >= 0 else max(0, length + end)
        return lst[s:e+1]

    async def expire(self, key, ttl):
        return True

    async def set(self, key, value, ex=None):
        self.store[key] = value
        return True

    async def get(self, key):
        return self.store.get(key)

    async def delete(self, *keys):
        count = 0
        for k in keys:
            if k in self.store:
                del self.store[k]
                count += 1
        return count

    async def aclose(self):
        pass


async def get_redis() -> aioredis.Redis:
    global redis_client
    if redis_client is None:
        try:
            client = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await client.ping()
            redis_client = client
            logger.info("redis_connected_successfully")
        except Exception as e:
            logger.warning("redis_connection_failed_using_mock", error=str(e))
            redis_client = MockRedis()
    return redis_client


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.aclose()
        redis_client = None
