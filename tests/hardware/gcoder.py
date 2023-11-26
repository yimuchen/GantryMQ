import logging
import time
from modules.gcoder import gcoder

logging.basicConfig(level=20)
logger = logging.getLogger('GantryMQ')

print("""
Expected behavior:

- The gantry will start up and move to home (this can be slow)
- The gantry will move to position (100, 100, 100)
- The gantry will move back to home

Program will then close nominally.
""")

## Testing the gcoder
g = gcoder('/dev/ttyUSB0')
g.move_to(100, 100, 100)
while g.in_motion():
  print(f"\r{g.cx:5.1f} {g.cy:5.1f} {g.cz:5.1f}", end='')
  time.sleep(0.1)
print('Done!')
