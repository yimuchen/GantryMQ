import logging
import time
from modules.drs import drs

logging.basicConfig(level=20)
logger = logging.getLogger('GantryMQ')

print("""
Expected behavior:

- Starting the DRS scope
- Running the voltage calibration routine (no output)
- Printing the time indexing values (length ~100 numpy array)

Program will then close nominally. Additional print-outs will be emitting from
the underlying libusb library:

libusb: warning [libusb_exit] device X.X still referenced
""")

## Testing the gcoder
drs_scope = drs()
d.run_calibration()
d.get_time_slice(0)
