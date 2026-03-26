from shared import server_data
import time

last_server_data = dict()
talking_points = []


def procedural_commentary_thread():
  while True:
    time.sleep(0.1)

    if not last_server_data:
      if server_data:
        last_server_data = server_data
        pass

    if 
  
    last_server_data = server_data
