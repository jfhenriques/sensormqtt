
from helpers.entity_runner import EntityRunner
from sensors.chia_wallet.chia_wallet_sensor import ChiaWalletSensor 



async def setup(e_id: str, runner: EntityRunner, config):

    if 'chia_wallet' not in config:
        raise Exception('chia_wallet section not found in config')

    certificate_file = config['chia_wallet']['certificate_file'] if 'certificate_file' in config['chia_wallet'] else None
    certificate_key = config['chia_wallet']['certificate_key'] if 'certificate_key' in config['chia_wallet'] else None
    host = config['chia_wallet']['host'] if 'host' in config['chia_wallet'] else 'localhost'
    port = config['chia_wallet']['port'] if 'port' in config['chia_wallet'] else 9256
    wallet_id = config['chia_wallet']['wallet_id'] if 'wallet_id' in config['chia_wallet'] else 1
    
    polling_rate = config['chia_wallet']['polling_rate'] if 'polling_rate' in config['chia_wallet'] else 600
    mqtt_topic = config['chia_wallet']['mqtt_topic'] if 'mqtt_topic' in config['chia_wallet'] else None
    
    sensor = ChiaWalletSensor(e_id, runner,
                                certificate_file = certificate_file,
                                certificate_key = certificate_key,
                                host = host,
                                port = port,
                                wallet_id = wallet_id,
                                mqtt_topic = mqtt_topic)

    await sensor.setup()

    runner.register_update_callback(sensor, sensor.update, None, polling_rate)

    return sensor



