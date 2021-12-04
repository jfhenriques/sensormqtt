
import sys, os
import psutil
import time
import subprocess
from helpers.entity_runner import EntityRunner
from util.util import *
from helpers.entity import Entity
from typing import List



RPI_TEMP_FILE = '/sys/class/thermal/thermal_zone0/temp'
RPI_THRO_FILE = '/sys/devices/platform/soc/soc:firmware/get_throttled'

# IO_COUNTER based on https://github.com/home-assistant/core/blob/dev/homeassistant/components/systemmonitor/sensor.py
IO_COUNTER = {
    "network_out": 0,
    "network_in": 1,
    "packets_out": 2,
    "packets_in": 3,
    "tp_net_out": 0,
    "tp_net_in": 1,
}


def get_cpu_temp():
   with open(RPI_TEMP_FILE, "r") as f:
      return round(int(f.readline()) / 1000, 1)

def get_throttled():
   _throttled = open(RPI_THRO_FILE, 'r').read()[:-1]
   return _throttled[:4]

def get_dir_size(path):
   try:
      return int(subprocess.check_output(['du','-sx', path]).split()[0].decode('utf-8'))
   except:
      return None


class SystemSensor(Entity):

   def __init__(self, e_id: str, runner: EntityRunner, *, is_rpi: bool = False, include_basic: bool = True, net_ifaces: List[str] = [], dir_list: List[str] = [], dir_refresh_rate = 600, mqtt_topic: str = None):
      super().__init__(e_id, "system", mqtt_topic)

      self.__runner: EntityRunner = runner

      self.__is_rpi: bool = sys.platform != "win32" and is_rpi
      self.__is_include_basic: bool = include_basic

      self.__net_ifaces: List[str] = net_ifaces
      self.__net_ifaces_last_check_time: float = None
      self.__net_ifaces_last: dict = {}
      self.__is_read_net_ifaces: bool = net_ifaces.__len__() > 0
      
      self.__dir_list: List[str] = dir_list
      self.__dir_last_check_date: float = None
      self.__dir_cache_sizes: dict = {}
      self.__is_read_dirs: bool = sys.platform != "win32" and dir_list.__len__() > 0
      self.__dir_refresh_rate: float = dir_refresh_rate

      self.__last_boot: str = None



   async def update(self):
      return await self.__runner.get_loop_handler().schedule_work(self.read_data)


   def read_data(self):

      reading = {}

      if self.__is_include_basic:
         self.__read_basic(reading)

      if self.__is_read_dirs:
         self.__read_dir_sizes(reading)

      if self.__is_read_net_ifaces:
         self.__read_net_ifaces(reading)

      return reading 

   def __read_basic(self, reading: dict):

      reading['processor_use'] = round(psutil.cpu_percent(interval=None))

      if sys.platform != "win32":
         reading['load_5'] = round(os.getloadavg()[1], 2)
         reading['load_15'] = round(os.getloadavg()[2], 2)

      if self.__is_rpi:
         reading['throttled'] = get_throttled()
         reading['cpu_temperature'] = get_cpu_temp()

      reading['memory_use_percent'] = psutil.virtual_memory().percent
      reading['swap_use_percent'] = psutil.swap_memory().percent
      reading['disk_use_percent'] = psutil.disk_usage('/').percent

      if self.__last_boot is None:
         self.__last_boot = utc_to_local(datetime.utcfromtimestamp(psutil.boot_time())).isoformat()

      reading['last_boot'] = self.__last_boot


   def __read_dir_sizes(self, reading: dict):

      cur_time = time.time()
      if self.__dir_last_check_date is None or (cur_time - self.__dir_last_check_date) >= self.__dir_refresh_rate:
         self.__dir_cache_sizes = {}

         for dir in self.__dir_list:
            self.__dir_cache_sizes[dir] = get_dir_size(dir)

         self.__dir_last_check_date = cur_time

         reading['dir_sizes'] = self.__dir_cache_sizes

      else:
         reading['dir_sizes'] = dict(self.__dir_cache_sizes)
            

   def __read_net_ifaces(self, reading: dict):

      net_ifaces = {}
      counters = psutil.net_io_counters(pernic=True)
      cur_time = time.time()

      secs_delta = (cur_time - self.__net_ifaces_last_check_time) if self.__net_ifaces_last_check_time is not None else None

      for i in self.__net_ifaces:

         if i in counters:

            for io in ['tp_net_in', 'tp_net_out']:

               state_key = '{}_{}'.format(i, io)
               counter = counters[i][IO_COUNTER[io]]
               last_i_io = self.__net_ifaces_last[state_key] if state_key in self.__net_ifaces_last else None
               cur_state = 0.0

               if last_i_io is not None and secs_delta is not None and last_i_io < counter:
                  cur_state = round( ( counter - last_i_io ) / 1000 ** 2 / secs_delta, 3)
               
               self.__net_ifaces_last[state_key] = counter
               net_ifaces[state_key] = cur_state                

      self.__net_ifaces_last_check_time = cur_time

      reading['net_ifaces'] = net_ifaces
