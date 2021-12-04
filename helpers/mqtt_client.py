
import asyncio
import paho.mqtt.client as mqtt
from util.util import *
from helpers.entity import Entity
from helpers.entity_runner import EntityRunner
import json
import tzlocal
import traceback
from util.consts import (
    BUS_EVENT_STATE_UPD,
    BUS_EVENT_STATE_UPD_NOW,
    DEFAULT_UPDATE_RATE
)


async def setup(e_id: str, runner: EntityRunner, config):

    print_ts('Conneting to mqtt broker...')

    client = MQTTClient(e_id, runner)

    result = await client.setup(config)
    if not result:
        print_error('Connecting to mqtt broker failed.')
        return None

    default_publish_interval = config['broker']['default_publish_interval'] if 'default_publish_interval' in config['broker'] else DEFAULT_UPDATE_RATE

    runner.register_update_callback(client, client.update, client.stop, default_publish_interval, 2)

    return client


class MQTTClient(Entity):

    def __init__(self, uuid: str, runner: EntityRunner):
        super().__init__(uuid, 'mqtt_broker')
        self.__runner: EntityRunner = runner
        self.__lock: asyncio.Lock = asyncio.Lock()
        self.__publish_queue: asyncio.Queue = asyncio.Queue()
        self.__publish_topic: str = None
        self.__mqtt_client:  mqtt.Client = None
        self.__state: dict = {}


    def _broker_on_connect(client, userdata, flags, rc):
        client.connected_flag = rc == 0
        client.connection_error_flag = rc != 0
        print_ts("Connected to mqtt broker with result code {}".format(rc))


    def validate_broker_config(config):
        default_publish_interval = config['broker']['default_publish_interval'] if 'default_publish_interval' in config['broker'] else None

        return 'broker' in config and \
                    'address' in config['broker'] and \
                    'port' in config['broker'] and \
                    'ttl' in config['broker'] and \
                    ( default_publish_interval == 0 or 'topic' in config['broker'] )

    async def __handle_update_normal_events(self, e_id: str = None, e_name: str = None, obj = {}):
        if e_name is not None:
            async with self.__lock:
                self.__state[e_name] = obj


    async def __handle_update_now_events(self, e_id: str = None, e_name: str = None, mqtt_topic: str = None, obj = {}):
        if e_name is not None and mqtt_topic is not None and obj:
            await self.__publish_queue.put( ( mqtt_topic, { e_name: obj } ) ) 


    async def __consume_queue(self):
        keep_looping = True
        # loop until None is received from the queue
        while keep_looping:
            try:
                queue_msg = await self.__publish_queue.get()
                self.__publish_queue.task_done()

                if not queue_msg:
                    # Ensure that if an execption occurs before the break, the loop won't continue
                    keep_looping = False
                    break

                if not isinstance(queue_msg, tuple) or len(queue_msg) != 2 or not all(queue_msg):
                    continue

                topic, msg = queue_msg

                msg['timestamp'] = datetime.now(tzlocal.get_localzone()).isoformat()
                await self.__runner.get_loop_handler().schedule_work(self.__mqtt_client.publish, topic, json.dumps(msg))

            except:
                print(traceback.format_exc())


    async def setup(self, config, timeout = 60):

        self.__publish_topic = config['broker']['topic'] if 'topic' in config['broker'] else None
        loop = self.__runner.get_event_loop()
        start_time = loop.time()

        def _setup_client():
            nonlocal self, config

            self.__mqtt_client = mqtt.Client()
            self.__mqtt_client.connected_flag = False
            self.__mqtt_client.connection_error_flag = False

            self.__mqtt_client.on_connect = MQTTClient._broker_on_connect
            self.__mqtt_client.connect(config['broker']['address'], config['broker']['port'], config['broker']['ttl'])
            self.__mqtt_client.loop_start()

        await self.__runner.get_loop_handler().schedule_work(_setup_client)
        
        while True:
            if self.__mqtt_client.connected_flag:
                break
            elif self.__mqtt_client.connection_error_flag or (loop.time() - start_time) > timeout:
                await self.stop()
                return False

            await asyncio.sleep(0.5)

        # Create queue consumer task
        self.__runner.get_event_loop().create_task( self.__consume_queue() )

        # Subscribe for normal event updates, that wait for the mqtt own update cycle to be published
        await self.__runner.get_event_bus().subscribe(BUS_EVENT_STATE_UPD, self.__handle_update_normal_events)

        # Subscrive for update now events, that are published right away
        await self.__runner.get_event_bus().subscribe(BUS_EVENT_STATE_UPD_NOW, self.__handle_update_now_events)

        return True
    
    async def stop(self):
        print_ts("Stopping mqtt client")
        try:
            await self.__publish_queue.put(None)
            await self.__publish_queue.join()
        except:
            print(traceback.format_exc())
        finally:
         await self.__runner.get_loop_handler().schedule_work(self.__mqtt_client.loop_stop)


    async def update(self):
        cur_state = None
        async with self.__lock:
            if not self.__state:
                return

            cur_state = self.__state
            self.__state = {}
        
        await self.__publish_queue.put( ( self.__publish_topic, cur_state ) )

