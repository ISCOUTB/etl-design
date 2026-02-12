import asyncio
from typing import Callable

from watchfiles import PythonFilter, arun_process


async def callback(changes):
    await asyncio.sleep(0.1)
    print("changes detected:", changes)


async def main_debug(
    main_function: Callable[[], None], debug_mode: bool = False
) -> None:
    if debug_mode:
        await arun_process(
            "./src",
            target=main_function,
            callback=callback,
            watch_filter=PythonFilter(),
        )
    else:
        main_function()
