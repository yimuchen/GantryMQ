import logging
from modules.i2c_mcp4725 import i2c_mcp4725
import time

logging.basicConfig(level=20)
logger = logging.getLogger("GantryMQ")

print(
    """
For the next 10 seconds, this will set the output voltage to ~4/5 of the working
voltage (5V)
"""
)

# Testing the I2C instance
c1 = i2c_mcp4725(1, 0x64)

for i in range(11):
    val = 409 + 1600 * (i + 1) // 10
    c1.set_int(val)
    print("Setting integer value to", val)
    print(c1.read_int())
    time.sleep(5)



# c2 = i2c_ads1115(1, 0x4A)
# print("Channel", 0, f"{c2.read_mv(0, i2c_ads1115.ADS_RANGE_6V):7.1f}", "[mV]")
# print("Channel", 1, f"{c2.read_mv(1, i2c_ads1115.ADS_RANGE_6V):7.1f}", "[mV]")
# print("Channel", 2, f"{c2.read_mv(2, i2c_ads1115.ADS_RANGE_6V):7.1f}", "[mV]")
# print("Channel", 3, f"{c2.read_mv(3, i2c_ads1115.ADS_RANGE_6V):7.1f}", "[mV]")
