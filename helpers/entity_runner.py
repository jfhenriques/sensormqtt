
import asyncio
import functools
from helpers.event_bus import EventBus
from helpers.loop_handler import LoopHandler
from helpers.entity import Entity
from typing import List
import signal
import functools
import os,sys
import traceback
from util.util import *
from util.consts import (
    BUS_EVENT_STATE_UPD,
    BUS_EVENT_STATE_UPD_NOW,
    FORCE_EXIT_MAX_COUNT
)


class EntityContext():

    def __init__(self):
        self.entity: Entity = None
        self.create_task_wrapper = None
        self.close_cb = None
        self.interval: float = None
        self.delay_start: float = 0
        self.start_run: float = None
        self.next_run: float = None
        self.running: bool = False
        self.on_complete = None
        self.coro = None
        self.task: asyncio.Task = None



class EntityRunner():

    def __init__(self, loop_handler: LoopHandler):
        self.__registry: List[EntityContext] = []
        self.__looping: bool = True
        self.__stopped: bool = False
        self.__shutdown_counter: int = FORCE_EXIT_MAX_COUNT
        self.__loop_handler: LoopHandler = loop_handler
        self.__stop_event: asyncio.Event = asyncio.Event()
        self.__event_bus: EventBus = EventBus(loop_handler.get_event_loop())

    def register_update_callback(self, entity: Entity, cb, close, interval: float, delay_start: float = 0):
        context = EntityContext()
        context.entity = entity
        context.interval = interval
        context.delay_start = delay_start
        context.close_cb = close

        if not isinstance(entity, Entity):
            return

        async def _cb_wrapper():
            nonlocal context

            if not self.__looping:
                return

            try:
                if context.delay_start > 0:
                    await asyncio.sleep( context.delay_start )
                    context.delay_start = 0

                context.start_run = context.next_run if context.next_run is not None else self.get_event_loop().time()
                context.running = True

                context.coro = cb()
                result = await context.coro

                if self.__looping and result is not None:
                    if context.entity.get_mqtt_topic() is None:
                        await self.__event_bus.publish(BUS_EVENT_STATE_UPD, context.entity.get_uuid(), context.entity.get_name(), result)
                    else:
                        await self.__event_bus.publish(BUS_EVENT_STATE_UPD_NOW, context.entity.get_uuid(), context.entity.get_name(), context.entity.get_mqtt_topic(), result)

            except:
                print(traceback.format_exc())

            # Ensure that if an error occurs, the next task is always scheduled
            finally:
                context.coro = None
                context.running = False

                # Schedule next run
                if self.__looping:
                    context.next_run = context.start_run + context.interval
                    if ( context.next_run - self.get_event_loop().time() ) > 0:
                        self.get_event_loop().call_at( context.next_run, context.create_task_wrapper )
                    else:
                        self.get_event_loop().call_soon( context.create_task_wrapper )

        def _create_task():
            nonlocal context
            context.task = self.get_event_loop().create_task( _cb_wrapper() )

        context.create_task_wrapper = _create_task

        self.__registry.append(context)


    def __register_signal_handler(self):
        loop = self.get_event_loop()

        for signame in ['SIGINT', 'SIGTERM']:
            if sys.platform == "win32":
                signal.signal(
                    getattr(signal, signame),
                    functools.partial(self.shutdown_handler, signame)
                )
            else:
                loop.add_signal_handler(
                    getattr(signal, signame),
                    functools.partial(self.shutdown_handler, signame)
                )

    def shutdown_handler(self, signal, *args):

        self.__shutdown_counter -= 1

        if self.__shutdown_counter == 0:
            print_ts("Force quiting...")
            os._exit(1) 

        elif (self.__shutdown_counter+1) < FORCE_EXIT_MAX_COUNT:
            print_ts("Already trying to stop. Hit Ctrl+C {} more time(s) to force quit...".format(self.__shutdown_counter))
            return

        print_ts("Received signal: {}, trying to exit...".format(signal))

        async def _try_stop():
            try:
                await self.stop_loop(60)

            except:
                print(traceback.format_exc())
        
        self.get_event_loop().create_task( _try_stop() )



    async def start_running(self):

        self.__register_signal_handler()

        self.__stopped = False
        self.__looping = True

        print_ts("Starting EntityRunner...")

        start_time = self.get_event_loop().time()

        # schedule the first run of every registred callback
        for context in self.__registry:
            if context.interval > 0:
                context.next_run = start_time + context.delay_start
                context.create_task_wrapper()
        
        # wait until the stop event is sent
        await self.__stop_event.wait()

        self.__looping = False

        print_ts("Stopping EntityRunner...")

        try:
            # Cancell all schedulled tasks not running
            for context in self.__registry:
                if not context.running and context.task is not None:
                    context.task.cancel()
        except:
            print(traceback.format_exc())


        await asyncio.sleep(0.1)

        running_tasks_count = 0
        start_time = self.get_event_loop().time()

        # wait 60 seconds for all contexts to be updated to not running
        while ( self.get_event_loop().time() - start_time ) < 60 :
            running_tasks_count = 0

            for context in self.__registry:
                if context.running:
                    running_tasks_count += 1
            if running_tasks_count == 0:
                break
            
            await asyncio.sleep(0.5)

        await asyncio.sleep(0.1)

        close_coros = []        
        for context in self.__registry:
            if context.close_cb is not None:
                close_coros.append( context.close_cb() )

        if close_coros.__len__() > 0:
            await asyncio.gather(*close_coros, return_exceptions = True)

        return True


    async def stop_loop(self, timeout: float = 15):
        if not self.__looping or self.__stopped:
            return

        self.__looping = False
        self.__stop_event.set()


    def get_loop_handler(self) -> LoopHandler:
        return self.__loop_handler

    def get_event_loop(self) -> asyncio.AbstractEventLoop:
        return self.__loop_handler.get_event_loop()

    def get_event_bus(self) -> EventBus:
        return self.__event_bus


                
                