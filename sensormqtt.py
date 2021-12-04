
import sys
import getopt
import util.config as conf
from util.util import *
from helpers.mqtt_client import MQTTClient
from helpers.entity_runner import EntityRunner
from helpers.entity_loader import EntityLoader
from helpers.loop_handler import LoopHandler
import functools
from util.consts import (
    DEFAULT_CONFIG_FILE
)


async def setup_run_async(loop_handler: LoopHandler, config):

    runner = EntityRunner(loop_handler)

    # Load entities
    print_ts("Start loading entities...")

    loader = EntityLoader(runner)
    await loader.load_entities(runner, config)
    
    print_ts("Finished loading entities")

    # Start the loop until and wait until finished
    return await runner.start_running()



def main(argv):

    # Start by reading the config
    config_file = DEFAULT_CONFIG_FILE

    opts, args = getopt.getopt(argv,"f:")
    for o,a in opts:
        if o == '-f':
            config_file = a
        
    config = conf.read_config_file(config_file)
    if config is not None:
        print_ts("Using configuration file: " + config_file)
    else:
        print_error("Please create config.yml file")
        return

    # Validate broker config and connect
    if not MQTTClient.validate_broker_config(config):
        print_error('Please define the broker section in config with elements: address, port, ttl, default_publish_interval = 0, or default_publish_interval > 0 and topic ')
        return

    # basic checks have passed, setup the loop handler and start running async
    loop_handler = LoopHandler()
    loop_handler.run(functools.partial(setup_run_async, loop_handler, config))

    # if reached here, program exited normally
    print_ts("Exited...")

# call main 
if __name__ == '__main__': 
  main(sys.argv[1:])

