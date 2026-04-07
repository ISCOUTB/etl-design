import asyncio
import time
from functools import wraps
from typing import Any, Callable, TypeVar

from src.utils.logger import logger

F = TypeVar("F", bound=Callable[..., Any])


def monitor_performance(operation_name: str):
    def decorator(func: F) -> F:
        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.perf_counter()

                try:
                    result = await func(*args, **kwargs)
                    status = "success"
                    return result
                except Exception as e:
                    status = "error"
                    raise e
                finally:
                    end_time = time.perf_counter()
                    duration = end_time - start_time

                    logger.info(
                        f"{operation_name} - Duration: {duration:.4f}s - Status: {status}"
                    )

            return async_wrapper
        else:

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.perf_counter()

                try:
                    result = func(*args, **kwargs)
                    status = "success"
                    return result
                except Exception as e:
                    status = "error"
                    raise e
                finally:
                    end_time = time.perf_counter()
                    duration = end_time - start_time

                    logger.info(
                        f"{operation_name} - Duration: {duration:.4f}s - Status: {status}"
                    )

            return sync_wrapper

    return decorator
