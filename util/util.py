from datetime import (
   datetime,
   timezone
)


#def write_file(file, t = 'N/A', h = 'N/A', p = None):
#   try:
#      f = open(file, 'w')
#   except:
#      print_error('Cannot open {}'.format(file))
#   else:
#      if p is not None:
#         f.write("T: {}°C  H: {}%  hPa: {}".format(t, h, p))
#      else:
#         f.write("T: {}°C  H: {}%".format(t, h))
#      f.close()


def print_ts(msg):
   ts = datetime.now()
   print("[{}] {}".format(ts, msg), flush=True)

def print_error(msg):
   print_ts("[ERROR] {}".format(msg))

def utc_to_local(utc_dt):
   return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)