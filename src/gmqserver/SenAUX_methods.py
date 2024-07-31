import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy

if "GMQPACKAGE_IS_CLIENT" not in os.environ:
    from zmq_server import HWBaseInstance

    from modules.gpio import gpio
    from modules.i2c_ads1115 import i2c_ads1115
else:
    from gmqclient.server.zmq_server import HWBaseInstance

    gpio = None
    i2c_ads1115 = None


class SenAUXDevice(HWBaseInstance):
    def __init__(self, name: str, logger: logging.Logger):
        super().__init__(name, logger)
        self.pd1_gpio: Union[bool, gpio] = False
        self.pd2_gpio: Union[bool, gpio] = False
        self.f1_gpio: Optional[gpio] = None
        self.f2_gpio: Optional[gpio] = None
        self.sen_adc: Optional[i2c_ads1115] = None
        self.resdiv_1: Tuple[float, float] = (10000, 0)
        self.resdiv_2: Tuple[float, float] = (10000, 0)
        self.resdiv_3: Tuple[float, float] = (10000, 0)

    def is_initialized(self):
        return True

    def is_dummy(self):
        return isinstance(self.f1_gpio, gpio)

    def reset_devices(self, device_json: Dict[str, Any]):
        """
        The configuration should be in the format should be something like:

        ```json
        {
             "SENAUX_PD1_GPIO": "22",
             "SENAUX_PD2_GPIO": "23",
             "SENAUX_F1_GPIO": "20",
             "SENAUX_F2_GPIO": "21",
             "SENAUX_ADC": {
                 "ADDR": "0x49",
                 "C1": [ 10000, 0 ],
                 "C2": [ 10000, 0 ],
                 "C3": [ 10000, 0 ],
             }
        }
        ```

        The GPIO pins correspond to the pin configurations used for each of
        output pins. The SENAUX_ADC.ADDR configuration should be the I2C
        address configuration of the sensor ADC, and SENAUX_AEC.CX should
        correspond to the resistor divider values on the system.
        """

        # Closing everything
        del self.pd1_gpio
        self.pd1_gpio = None
        del self.pd2_gpio
        self.pd2_gpio = None
        del self.f1_gpio
        self.f1_gpio = None
        del self.f2_gpio
        self.f2_gpio = None
        del self.sen_adc
        self.sen_adc = None

        # Checking in the input format
        assert isinstance(device_json, dict)
        assert "SENAUX_PD1_GPIO" in device_json
        assert "SENAUX_PD2_GPIO" in device_json
        assert "SENAUX_F1_GPIO" in device_json
        assert "SENAUX_F2_GPIO" in device_json
        assert "SENAUX_ADC" in device_json
        assert "ADDR" in device_json["SENAUX_ADC"]
        assert "C1" in device_json["SENAUX_ADC"]
        assert "C2" in device_json["SENAUX_ADC"]
        assert "C3" in device_json["SENAUX_ADC"]
        assert len(device_json["SENAUX_ADC"]["C1"]) == 2
        assert len(device_json["SENAUX_ADC"]["C2"]) == 2
        assert len(device_json["SENAUX_ADC"]["C3"]) == 2

        # Checking if any configuration is requesting a dummy configuration
        is_dummy = any(
            [
                x.lower() == "dummy"
                for x in [
                    device_json["SENAUX_PD1_GPIO"],
                    device_json["SENAUX_PD2_GPIO"],
                    device_json["SENAUX_F1_GPIO"],
                    device_json["SENAUX_F2_GPIO"],
                    device_json["SENAUX_ADC"]["ADDR"],
                ]
            ]
        )
        if is_dummy:
            self.pd1_gpio = False
            self.pd2_gpio = False
            self.f1_gpio = None
            self.f2_gpio = None
            self.sen_adc = None
        else:
            self.pd1_gpio = gpio(int(device_json["SENAUX_PD1_GPIO"]), gpio.READ_WRITE)
            self.pd2_gpio = gpio(int(device_json["SENAUX_PD2_GPIO"]), gpio.READ_WRITE)
            self.f1_gpio = gpio(int(device_json["SENAUX_F1_GPIO"]), gpio.READ_WRITE)
            self.f2_gpio = gpio(int(device_json["SENAUX_F2_GPIO"]), gpio.READ_WRITE)
            self.sen_adc = i2c_ads1115(
                1, int(device_json["SENAUX_ADC"]["ADDR"], base=16)
            )
            self.resdiv_1 = tuple(device_json["SENAUX_ADC"]["C1"])
            self.resdiv_2 = tuple(device_json["SENAUX_ADC"]["C2"])
            self.resdiv_3 = tuple(device_json["SENAUX_ADC"]["C3"])

    @classmethod
    def _write_gpio(cls, dev: Union[bool, gpio], val: bool):
        """Helper method for dummy device processing"""
        if isinstance(dev, gpio):
            dev.slow_write(val)
        else:
            dev = val

    @classmethod
    def _stat_gpio(cls, dev: Union[bool, gpio]) -> bool:
        """Helper method for dummy device"""
        if isinstance(dev, gpio):
            return dev.read()
        else:
            return dev

    def enable_pd1(self):
        """Enabling the power rail connected to power port channel 1"""
        self._write_gpio(self.pd1_gpio, True)

    def disable_pd1(self):
        """Disabling the power rail connected to power port channel 1"""
        self._write_gpio(self.pd1_gpio, False)

    def status_pd1(self) -> bool:
        """Checking the status of power rail on channel 1"""
        return self._stat_gpio(self.pd1_gpio)

    def enable_pd2(self):
        """Enabling the power rail connected to power port channel 2"""
        self._write_gpio(self.pd1_gpio, True)

    def disable_pd2(self):
        """Disabling the power rail connected to power port channel 2"""
        self._write_gpio(self.pd1_gpio, False)

    def status_pd2(self) -> bool:
        """Checking the status of power rail on channel 2"""
        return self._stat_gpio(self.pd1_gpio)

    @classmethod
    def _pulse_gpio(cls, dev: Union[bool, gpio], n: int, wait: int):
        if isinstance(dev, gpio):
            dev.pulse(n=n, wait=wait)

    def pulse_f1(self, n: int, w: int):
        """Pulsing the fast port 1, for n times, waiting for w microseconds"""
        self._pulse_gpio(self.f1_gpio, n, w)

    def pulse_f2(self, n: int, w: int):
        """Pulsing the fast port 2, for n times, waiting for w microseconds"""
        self._pulse_gpio(self.f2_gpio, n, w)

    def adc_readmv(self, channel: int) -> float:
        """Reading the ADC voltage readout values of a particular channel"""
        assert 0 <= channel <= 3
        if isinstance(self.sen_adc, i2c_ads1115):
            return self.sen_adc.read_mv(channel, i2c_ads1115.ADS_RANGE_6V)
        else:
            return numpy.random.normal(2500, 300 * channel)

    def adc_biasresistor(self, channel: int) -> Tuple[float, float]:
        """Returning the resistor configurations values of a particular channel"""
        assert 1 <= channel <= 3
        return getattr(self, "resdiv_" + str(channel))

    @property
    def telemetry_methods(self) -> List[str]:
        return [
            "status_pd1",
            "status_pd2",
            "adc_readmv",
            "adc_biasresistor",
        ]

    @property
    def operation_methods(self) -> List[str]:
        return [
            "reset_devices",
            "enable_pd1",
            "disable_pd1",
            "enable_pd2",
            "disable_pd2",
            "pulse_f1",
            "pulse_f2",
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

    # Declaring a dummy device

    # Declaring logging to keep everything by default
    logging.root.setLevel(logging.NOTSET)
    logging.basicConfig(level=logging.NOTSET)
    logger = logging.getLogger("TestSenAUXMethods")

    # Creating hardware controller
    senaux = SenAUXDevice("senaux", logger)
    senaux.reset_devices(config)

    # Creating the server instance
    server = HWControlServer(
        make_zmq_server_socket(config["port"]),
        logger=logger,
        hw_list=[senaux],
    )

    # Running the server
    server.run_server()
