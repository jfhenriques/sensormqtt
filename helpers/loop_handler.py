
import asyncio
import concurrent.futures
import threading
from util.consts import (
    MAX_WORKERS
)

import contextlib

class LoopHandler(object):

    def __init__(self):
        self.__loop: asyncio.AbstractEventLoop = None
        self.__pool: concurrent.futures.ThreadPoolExecutor = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self.__loop = loop
    def get_event_loop(self) -> asyncio.AbstractEventLoop:
        return self.__loop

    def set_pool(self, pool: concurrent.futures.ThreadPoolExecutor) -> None:
        self.__pool = pool
    def get_pool(self) -> concurrent.futures.ThreadPoolExecutor:
        return self.__pool


    def schedule_work(self, cb, *args) -> asyncio.Future:
        return self.__loop.run_in_executor(self.__pool, cb, *args)

    def run(self, fn):
        asyncio.set_event_loop_policy(HandlerEventLoopPolicy(self))

        return asyncio.run(fn())

    @contextlib.asynccontextmanager
    async def async_lock(self, lock: threading.Lock):
        await self.__loop.run_in_executor(self.__loop, lock.acquire)
        try:
            yield  # the lock is held
        finally:
            lock.release()



# based on HassEventLoopPolicy https://github.com/home-assistant/core/blob/cbbf22db52f19b8ba77769352fc020460eb358ca/homeassistant/runner.py#L53

class HandlerEventLoopPolicy(asyncio.DefaultEventLoopPolicy): 

    def __init__(self, handler: LoopHandler):
        super().__init__()
        self.__loop_handler: LoopHandler = handler

    def new_event_loop(self) -> asyncio.AbstractEventLoop:
        """create new event loop."""
        loop: asyncio.AbstractEventLoop = super().new_event_loop()

        executor = concurrent.futures.ThreadPoolExecutor(
            thread_name_prefix = "EntityWorker",
            max_workers = MAX_WORKERS
        )

        loop.set_default_executor(executor)

        self.__loop_handler.set_event_loop(loop)
        self.__loop_handler.set_pool(executor)

        return loop
