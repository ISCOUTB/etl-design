import asyncio
from typing import Callable

from watchfiles import PythonFilter, arun_process

from src.utils.logger import logger


async def callback(changes):
    await asyncio.sleep(0.1)
    logger.debug("changes detected:", changes)


async def main_debug(main_function: Callable[[], None]) -> None:
    await arun_process(
        "./src",
        target=main_function,
        callback=callback,
        watch_filter=PythonFilter(),
    )
