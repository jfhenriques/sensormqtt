
import yaml
from util.util import *


def read_config_file(config_file):
   try:
      return yaml.load(open(config_file, 'r'), Loader=yaml.FullLoader)
      
   except:
      return None