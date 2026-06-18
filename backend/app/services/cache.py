"""
Redis-backed caching and rate limiting.

Design principle: Redis is an OPTIMISATION, not a hard dependency. Every function
degrades gracefully — if Redis is unreachable, rate limits allow the request and
cache reads miss. The app keeps working; it just loses the speed/protection benefit.
"""
import json
from typing import Optional
from app.config import settings

_redis = None
_redis_unavailable = False


async def get_redis():
    """Lazily connect to Redis. Returns None if unavailable (cached after first failure)."""
    global _redis, _redis_unavailable
    if _redis_unavailable:
        return None
    if _redis is not None:
        return _redis
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        await client.ping()
        _redis = client
        return _redis
    except Exception:
        _redis_unavailable = True
        return None


async def rate_limit(key: str, limit: int, window_seconds: int) -> bool:
    """
    Fixed-window rate limiter. Returns True if the request is ALLOWED.
    Fails open: if Redis is down, always allows (we don't lock users out over infra).
    """
    r = await get_redis()
    if r is None:
        return True
    try:
        full_key = f"ratelimit:{key}"
        count = await r.incr(full_key)
        if count == 1:
            await r.expire(full_key, window_seconds)
        return count <= limit
    except Exception:
        return True


async def cache_get(key: str):
    """Returns the cached JSON value, or None on miss / Redis unavailable."""
    r = await get_redis()
    if r is None:
        return None
    try:
        raw = await r.get(f"cache:{key}")
        return json.loads(raw) if raw else None
    except Exception:
        return None


async def cache_set(key: str, value, ttl_seconds: int = 300):
    """Stores a JSON-serialisable value. Silent no-op if Redis is unavailable."""
    r = await get_redis()
    if r is None:
        return
    try:
        await r.set(f"cache:{key}", json.dumps(value), ex=ttl_seconds)
    except Exception:
        pass


async def cache_invalidate(key: str):
    r = await get_redis()
    if r is None:
        return
    try:
        await r.delete(f"cache:{key}")
    except Exception:
        pass
