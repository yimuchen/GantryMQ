import logging
from modules.gpio import gpio

logging.basicConfig(level=20)
logger = logging.getLogger('GantryMQ')
logger.setLevel(6)

print("""
Expected behavior:

- The GPIO pin 21 (phyiscal pin 40) will pulse 100 times. (No stdout output)

Program will then close nominally.
""")

## Testing the GPIO -- A trigger-like pin on GPIO pin 21 (physical pin 40)
trigger_gpio = gpio(21, gpio.WRITE)
trigger_gpio.pulse(100, 1000)
