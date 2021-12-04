import asyncio
from typing import List


# class EventHook based from https://stackoverflow.com/a/1094423
class EventHook(object):

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.__loop: asyncio.AbstractEventLoop = loop
        self.__coros: List = []

    def __iadd__(self, coro):
        self.__coros.append(coro)
        return self

    def __isub__(self, coro):
        self.__coros.remove(coro)
        return self

    async def fire(self, *args, **keywargs):
        for cb in self.__coros:
            #await cb(*args, **keywargs)
            self.__loop.create_task( cb(*args, **keywargs) )


class EventBus():

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.__events: dict = {}
        self.__loop: asyncio.AbstractEventLoop = loop
        self.__lock: asyncio.Lock = asyncio.Lock()

    async def subscribe(self, event: str, cb):
        hook = None
        async with self.__lock:
            if event in self.__events:
                hook = self.__events[event]
            else:
                hook = EventHook(self.__loop)
                self.__events[event] = hook
            hook += cb
        return True

    async def remove(self, event, cb):
        async with self.__lock:
            if event in self.__events:
                self.__events[event] -= cb
                return True
        return False

    async def publish(self, event, *args, **keywargs):
        if event in self.__events:
            return await self.__events[event].fire(*args, **keywargs)
        return False



