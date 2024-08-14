import json
import logging
import os
from typing import Any, Dict, List, Optional

if "GMQPACKAGE_IS_CLIENT" not in os.environ:
    from zmq_server import HWBaseInstance

    from modules.gpio import gpio
    from modules.i2c_ads1115 import i2c_ads1115
    from modules.i2c_mcp4725 import i2c_mcp4725
else:
    from gmqclient.server.zmq_server import HWBaseInstance

    drs = None  # Adding a dummy global variable


class HVLVDevice(HWBaseInstance):
    def __init__(self, name: str, logger: logging.Logger):
        super().__init__(name, logger)
        # Setting up  the various items
        self.hv_gpio: Optional[gpio] = None
        self.hvlv_adc: Optional[i2c_ads1115] = None
        self.hv_dac: Optional[i2c_mcp4725] = None
        self.lv_dac: Optional[i2c_mcp4725] = None

    def is_initialized(self):
        return True  # Always available to receive

    def is_dummy(self):
        return any(
            x is None for x in [self.hv_gpio, self.hvlv_adc, self.hv_dac, self.lv_dac]
        )

    def reset_devices(self, dev_conf: Dict[str, Any]):
        """
        As multiple devices needs to exist, to avoid a verbose function, the
        input will be path to JSON file to be parsed, or a dictionary of the
        same format. It should be place in the format:

            ```json { "HV_ENABLE_GPIO": "27", # GPIO PIN NUMBER, base 10
                     "HVLV_ADC_ADDR": "0x48", # I2C address on bus 1, base 16
                     "HV_DAC_ADDR": "0x64",   # I2C address on bus 1, base 16
                     "LV_DAC_ADDR": "0x65"    # I2C address on bus 1, base 16 }
            ```

        Notice that if any 1 of the entries here is listed as "dummy", case
        insensitive, the entire item will be listed as a dummy device.
        """
        # Closing all devices
        if self.hv_gpio is not None:
            del self.hv_gpio
            self.hv_gpio = None
        if self.hvlv_adc is not None:
            del self.hvlv_adc
            self.hvlv_adc = None
        if self.hv_dac is not None:
            del self.hv_dac
            self.hv_dac = None
        if self.lv_dac is not None:
            del self.lv_dac
            self.lv_dac = None

        # Checking if the given configuration is correct
        if isinstance(dev_conf, str):
            dev_conf = json.load(open(dev_conf, "r"))
        if not isinstance(dev_conf, dict):
            raise ValueError(f"Unknown type [{type(dev_conf)}] used for initialization")

        assert "HV_ENABLE_GPIO" in dev_conf
        assert "HVLV_ADC_ADDR" in dev_conf
        assert "HV_DAC_ADDR" in dev_conf
        assert "LV_DAC_ADDR" in dev_conf

        # Checking if the configuration should be flagged as a dummy device
        set_dummy = any(
            x.lower() == "dummy"
            for x in [
                dev_conf["HV_ENABLE_GPIO"],
                dev_conf["HVLV_ADC_ADDR"],
                dev_conf["HV_DAC_ADDR"],
                dev_conf["LV_DAC_ADDR"],
            ]
        )

        if not set_dummy:
            self.hv_gpio = gpio(int(dev_conf["HV_ENABLE_GPIO"]))
            self.hvlv_adc = i2c_ads1115(1, int(dev_conf["HVLV_ADC_ADDR"], base=16))
            self.hv_dac = i2c_mcp4725(1, int(dev_conf["HV_DAC_ADDR"], base=16))
            self.lv_dac = i2c_mcp4725(1, int(dev_conf["LV_DAC_ADDR"], base=16))

            # Disable HV on start up
            self.hv_gpio.write(0)
        else:
            self.hv_gpio = None
            self.hvlv_adc = None
            self.hv_dac = None
            self.lv_dac = None

    def hv_enable(self):
        """Enable the high-voltage power rail"""
        if not self.is_dummy():
            self.hv_gpio.write(True)
        else:
            self.hv_gpio = True

    def hv_disable(self):
        """Disable the high-voltage power rail"""
        if not self.is_dummy():
            self.hv_gpio.write(False)
        else:
            self.hv_gpio = False

    def get_hv_status(self) -> bool:
        """Checking if the high-voltage power rail"""
        if not self.is_dummy():
            return self.hv_gpio.read()
        else:
            return self.hv_gpio

    def set_hv_control_mv(self, target: float):
        """
        Setting the control voltage for adjusting the high-voltage rail, units
        in mV
        """
        # TODO: Handle proper operation of VDD
        assert 0 <= target <= 5000
        vdd = self.get_vdd_mv()
        if not self.is_dummy():
            self.hv_dac.set_int(int(4095 * float(target / vdd)))
        else:
            self.hv_dac = target

    def set_lv_mv(self, target: float):
        """Setting the low-voltage rail value. Units in mV"""
        # TODO: Handle proper operation of VDD
        assert 0 <= target <= 5000
        vdd = self.get_vdd_mv()
        if not self.is_dummy():
            self.lv_dac.set_int(int(4095 * float(target / vdd)))
        else:
            self.lv_dac = target

    def get_hv_mv(self) -> float:
        """Returning the high-voltage rail voltage value. Units in mV"""
        if not self.is_dummy():
            # TODO: 101 from multiple divider values. Programmable??
            return self.hvlv_adc.read_mv(0, i2c_ads1115.ADS_RANGE_1V) * 101
        else:
            if self.get_hv_status():
                # TODO better indirect estimate based on control voltage
                return 70
            else:
                return 0

    def get_hv_control_mv(self) -> float:
        """Returning the high-voltage rail control voltage. Units in mV"""
        if not self.is_dummy():
            return self.hvlv_adc.read_mv(1, i2c_ads1115.ADS_RANGE_4V)
        else:
            return self.hv_dac

    def get_lv_mv(self) -> float:
        """Returning the low-voltage rail voltage. Units in mV"""
        if not self.is_dummy():
            # TODO: Cannot read this due to hardware design flaw. Using DAC
            # register value as a work around

            # return self.hvlv_adc.read_mv(2, i2c_ads1115.ADS_RANGE_4V)
            return self.get_vdd_mv() * self.lv_dac.read_int() / 4096.0
        else:
            return self.lv_dac

    def get_vdd_mv(self) -> float:
        """Returning the primary power rail voltage. Units in mV"""
        if not self.is_dummy():
            return self.hvlv_adc.read_mv(3, i2c_ads1115.ADS_RANGE_6V)
        else:
            return 5000

    @property
    def telemetry_methods(self) -> List[str]:
        return [
            "get_hv_status",
            "get_hv_mv",
            "get_hv_control_mv",
            "get_lv_mv",
            "get_vdd_mv",
        ]

    @property
    def operation_methods(self) -> List[str]:
        return [
            "reset_devices",
            "hv_enable",
            "hv_disable",
            "set_hv_control_mv",
            "set_lv_mv",
        ]


if __name__ == "__main__":
    from zmq_server import (
        HWControlServer,
        make_cmd_parser,
        make_zmq_server_socket,
        parse_cmd_args,
    )

    parser = make_cmd_parser("camera_methods.py", "Test server for camera operations")
    config = parse_cmd_args(parser)

    # Declaring logging to keep everything by default
    logging.root.setLevel(logging.NOTSET)
    logging.basicConfig(level=logging.NOTSET)
    logger = logging.getLogger("TestHVLVMethods")

    hvlv = HVLVDevice("hvlv", logger)
    hvlv.reset_devices(config)

    # Creating the server instance
    server = HWControlServer(
        socket=make_zmq_server_socket(config["port"]),
        logger=logger,
        hw_list=[hvlv],
    )

    # Running the server
    server.run_server()
