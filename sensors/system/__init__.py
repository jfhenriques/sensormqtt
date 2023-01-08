
from helpers.entity_runner import EntityRunner
from sensors.system.system_sensor import SystemSensor
from util.consts import (
    DEFAULT_UPDATE_RATE
)


async def setup(e_id: str, runner: EntityRunner, config):

    if 'system' not in config:
        config['system'] = []

    is_rpi = config['system']['is_rpi'] if 'is_rpi' in config['system'] else False
    dir_list = config['system']['dir_list'] if 'dir_list' in config['system'] else []
    disk_list = config['system']['disk_list'] if 'disk_list' in config['system'] else []
    dir_refresh_rate = config['system']['dir_refresh_rate'] if 'dir_refresh_rate' in config['system'] else 600
    net_ifaces = config['system']['net_ifaces'] if 'net_ifaces' in config['system'] else []
    include_basic = config['system']['read_basic'] if 'read_basic' in config['system'] else False
    polling_rate = config['system']['polling_rate'] if 'polling_rate' in config['system'] else DEFAULT_UPDATE_RATE
    mqtt_topic = config['system']['mqtt_topic'] if 'mqtt_topic' in config['system'] else None
    cpu_temp_file = config['system']['cpu_temp_file'] if 'cpu_temp_file' in config['system'] else None
    cpu_rpm_file = config['system']['cpu_rpm_file'] if 'cpu_rpm_file' in config['system'] else None
    
    sensor = SystemSensor(e_id, runner,
                            is_rpi = is_rpi,
                            include_basic = include_basic,
                            net_ifaces = net_ifaces,
                            dir_list = dir_list,
                            dir_refresh_rate = dir_refresh_rate,
                            mqtt_topic = mqtt_topic,
                            cpu_temp_file = cpu_temp_file,
                            disk_list = disk_list,
                            cpu_rpm_file = cpu_rpm_file)

    runner.register_update_callback(sensor, sensor.update, None, polling_rate)

    return sensor
