from abc import ABC
from typing import TypeVar

from src.core.config import settings
from src.core.connection_manager import get_connection_manager

RequestT = TypeVar("RequestT", contravariant=True)
ResponseT = TypeVar("ResponseT", covariant=True)


class BaseHandler(ABC):
    def __init__(self):
        super().__init__()
        self.manager = get_connection_manager()
        self.max_retries_redis: int = settings.REDIS_MAX_RETRIES
        self.retry_delay_redis: float = settings.REDIS_RETRY_DELAY_SECONDS
        self.backoff_redis: float = settings.REDIS_RETRY_BACKOFF_FACTOR

        self.max_retries_mongo: int = settings.MONGO_MAX_RETRIES
        self.retry_delay_mongo: float = settings.MONGO_RETRY_DELAY_SECONDS
        self.backoff_mongo: float = settings.MONGO_RETRY_BACKOFF_FACTOR
