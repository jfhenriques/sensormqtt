# sensormqtt

Sensor engine, inspired and initially created to be used with Home Assistant

All data collected from the sensors is published to a MQTT Broker

Testing was done with:
- Python: with python 3.7 and above (arm and x86_64)
- MQTT Broker: mosquitto v2.0.11


## Supported sensors

Currently, two sensors are supported

- **System**: collects data from the system (CPU, Ram, Disk, network usage, etc.)
- **Chia Wallet**: Get the balance and status of a chia wallet. Requires chia blockchain to be setup and running locally (or in the network). Connects to the Chia RPC Interface (access to the cert and private key is needed)

New sensors can be easily created. For example, to create a TimeSensor:
- Create a directory *sensors/time*
- Create *\_\_init\_\_.py* inside *sensors/time*
- Define the async setup function inside *\_\_init\_\_.py* (check implementation of *sensors/system*)
- Import the sensor in the configuration file in the *sensors* section list: "- time"
- Restart *sensormqtt*

**Note**: if additional configuration is needed to setup the sensor, it is recommended to use a section with the same name **time** in the config file

## Installation

A virtual env is recommended

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```


## Configuration

```bash
cp example.config.yml config.yml
```

## Sample config

```yaml
# Uncomment sensors below to activate
sensors:
- system
#- chia_wallet

# Internal broker sensor
#  Will aggregate and send all other sensor's readings to the mqtt broker
broker:

  address: '192.168.0.35'
  port: 1883
  ttl: 60

  # Configures the update interval to the mqtt broker
  #  Set as 0 to disable (all sensors will require their own mqtt_topic section defined)
  default_publish_interval: 0

  # Default mqtt topic for the internal broker sensor
  #  Sensors that don't provide their own mqtt_topic, will have their readings aggregated and published at once
  #  Required if default_publish_interval > 0
  topic: 'ha/test/sensor/aggregated'


# System sensor
system:

  # Polling rate to get the metrics
  #   Defaults to 10 when omitted
  polling_rate: 10

  # System mqtt topic
  #  Comment to use the aggregated broker publish
  mqtt_topic: 'ha/test/sensor/system'

  # Read basic metrics: cpu, memory, etc
  #   Defaults to False when omitted
  read_basic: True

  # Uncomment to read CPU temperature and throttle status, if running in the raspbery pi
  #   Defaults to False when omitted
  #is_rpi: True

  # List of network interfaces to collect network usage
  #   Comment section to disable
  net_ifaces:
  - eth0

  # List of directories to monitor the space used
  #   Only works on linux
  #   Comment section to disable
  dir_list:
  - /var/log

  # Seconds interval for checking the space of dir_list
  #   Checking the occupied space of a directory is CPU intensive,
  #   it is recommended to use an higher interval that the sensor's polling_rate
  #   Data is cached in normal reads, and only updated if dir_refresh_rate seconds have passed
  #   Defaults to 600 seconds (10 minutes) when omitted
  dir_refresh_rate: 600


# Chia sensor
chia_wallet:

  # Polling rate to get the metrics
  #   Defaults to 10 when omitted
  polling_rate: 10

  # System mqtt topic
  #  Comment to use the aggregated broker publish
  mqtt_topic: 'ha/test/sensor/chia'

  # Chia Wallet Certificate
  #   Chia wallet requires all RPC calls to be done with using the certificate and private key
  #   User running the sensormqtt needs to have access to the certificate
  certificate_file: '/home/user/.chia/mainnet/config/ssl/wallet/private_wallet.crt'

  # Chia Wallet Private Key
  #   Chia wallet requires all RPC calls to be done with using the certificate and private key
  #   User running the sensormqtt needs to have access to the private key
  certificate_key: '/home/user/.chia/mainnet/config/ssl/wallet/private_wallet.key'

  # Host running the RPC Wallet
  #   Default to localhost
  host: 'localhost'

  # Port of the the RPC Wallet
  #   Default to 9256
  port: 9256

  # wallet id
  #   Default to 1
  chia_wallet_id: 1
```

## Example json data sent to the broker
```json
{
    "timestamp": "2021-11-29T18:58:06.237678+00:00",
    "system": {
        "processor_use": 0,
        "last_boot": "2020-07-29T16:30:03+01:00",
        "cpu_temperature": 50.5,
        "memory_use_percent": 14.1,
        "dir_sizes": {
            "/var/log": 15676
        },
        "throttled": "0",
        "load_15": 0.0,
        "disk_use_percent": 25.0,
        "load_5": 0.0,
        "swap_use_percent": 1.0,
        "net_ifaces": {
            "eth0_tp_net_out": 0.002,
            "eth0_tp_net_in": 0.001
        }
    },
    "chia_wallet": {
        "wallet_balance_1": {
            "confirmed_wallet_balance": 0,
            "max_send_amount": 0,
            "pending_change": 0,
            "pending_coin_removal_count": 0,
            "spendable_balance": 0,
            "unconfirmed_wallet_balance": 0,
            "unspent_coin_count": 0,
            "wallet_id": 1
        },
        "wallet_sync_status": {
            "genesis_initialized": true,
            "success": true,
            "synced": true,
            "syncing": false
        }
    }
}
```

**Note**: Wallet id is suffixed in the reading name: *wallet_ballance_1* for walled id 1

## Run as a service

```bash
cp example.sensormqtt.service /etc/systemd/system/sensormqtt.service
```
Modify the *ExecStart* and *WorkingDirectory* in */etc/systemd/system/sensormqtt.service* with your favorite editor

```bash
systemctl daemon-reload
systemctl enable --now sensormqtt.service
```

# Limitations
- Mqtt user and password is not supported yet when connecting to the broker
- No multiple instances of the same sensor (like configuring multiple template sensors in home assistant)
- if default_publish_interval == 0 and sensors don't provide their own mqtt_topic, the readings will never be published
