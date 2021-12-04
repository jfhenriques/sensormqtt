
import importlib
from helpers.entity import Entity
from util.util import *
import asyncio
from helpers.entity_runner import EntityRunner
import uuid
from typing import List




# TODO: support to unregister entities

class EntityLoader():

    def __init__(self, runner: asyncio.AbstractEventLoop):
        self.__entities = {}
        self.__runner: EntityRunner = runner

    def get_sensors(self):
        return self.__entities

    async def load_entities(self, runner: EntityRunner, config = []):

        to_load = []

        # gather sensors defined in config
        if 'sensors' in config:
            for s in config['sensors']:
                to_load.append( 'sensors.{}'.format(s) )

        # inject the mqtt broker client
        to_load.append('helpers.mqtt_client')

        coros = []
        for e in to_load:
            e_id = uuid.uuid4().__str__()
            self.__entities[e_id] = None
            coro = importlib.import_module(e).setup(e_id, self.__runner, config)
            coros.append(coro)

        if coros.__len__() > 0:
            entities: List[Entity] = await asyncio.gather(*coros)
            for entity in entities:
                e_id = entity.get_uuid()
                if e_id is not None:
                    self.__entities[e_id] = entity
