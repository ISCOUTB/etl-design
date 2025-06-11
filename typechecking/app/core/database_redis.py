from typing import Any
from redis import Redis
from app.core.config import settings


redis_client = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD,
    decode_responses=True,
)


def set(key: str, value: Any, ex: int = None) -> None:
    redis_client.set(key, value, ex=ex)


def get(key: str) -> Any | None:
    """
    Retrieve a value from the Redis cache by key.
    If the key does not exist, it returns None.
    """
    return redis_client.get(key)


def delete(*keys: str) -> int:
    """
    Delete a key from the Redis cache.
    """
    return redis_client.delete(*keys)


# Functions to manage the all Redis cache
def get_cache() -> dict[str, Any]:
    """
    Retrieve all keys and values from the Redis cache.
    """
    keys = redis_client.keys("*")
    values = redis_client.mget(keys)
    return dict(zip(keys, values))


def clear_cache() -> Any:
    return redis_client.flushdb()
