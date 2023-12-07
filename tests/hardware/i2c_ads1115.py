import logging
from modules.i2c_ads1115 import i2c_ads1115

logging.basicConfig(level=20)
logger = logging.getLogger("GantryMQ")

print(
    """
Expected behavior:

- Prints 4 lines, corresponding to the voltage levels of the 4 input channels.

Program will then close nominally.
"""
)

# Testing the I2C instance
c1 = i2c_ads1115(1, 0x48)
print("Channel", 0, f"{c1.read_mv(0, i2c_ads1115.ADS_RANGE_4V):7.1f}", "[mV]")
print("Channel", 1, f"{c1.read_mv(1, i2c_ads1115.ADS_RANGE_4V):7.1f}", "[mV]")
print("Channel", 2, f"{c1.read_mv(2, i2c_ads1115.ADS_RANGE_4V):7.1f}", "[mV]")
print("Channel", 3, f"{c1.read_mv(3, i2c_ads1115.ADS_RANGE_4V):7.1f}", "[mV]")

# c2 = i2c_ads1115(1, 0x4A)
# print("Channel", 0, f"{c2.read_mv(0, i2c_ads1115.ADS_RANGE_6V):7.1f}", "[mV]")
# print("Channel", 1, f"{c2.read_mv(1, i2c_ads1115.ADS_RANGE_6V):7.1f}", "[mV]")
# print("Channel", 2, f"{c2.read_mv(2, i2c_ads1115.ADS_RANGE_6V):7.1f}", "[mV]")
# print("Channel", 3, f"{c2.read_mv(3, i2c_ads1115.ADS_RANGE_6V):7.1f}", "[mV]")
