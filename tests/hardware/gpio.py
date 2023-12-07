import logging
from modules.gpio import gpio
import time

logging.basicConfig(level=20)
logger = logging.getLogger("GantryMQ")

print(
    """
Expected behavior:

- The GPIO pin 21 (physical pin 40) will pulse 100 times. (No stdout output)
- The GPIO pin 27 (physical pin X) will toggle on for 5 seconds, the toggle off again

Program will then close nominally.
"""
)

## Testing the GPIO -- A trigger-like pin on GPIO pin 21 (physical pin 40)
trigger_gpio = gpio(21, gpio.WRITE)
trigger_gpio.pulse(100, 1000)

hv_gpio = gpio(27, gpio.WRITE)
hv_gpio.slow_write(True)
time.sleep(5)
hv_gpio.slow_write(False)
