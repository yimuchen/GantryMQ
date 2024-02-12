import json
import logging
from typing import Dict, Tuple, Union

import numpy
from modules.gpio import gpio
from modules.i2c_ads1115 import i2c_ads1115
from zmq_server import HWContainer


def reset_senaux_devices(
    logger: logging.Logger, hw: HWContainer, device_json: Union[str, Dict[str, str]]
):
    """
    As multiple devices needs to exist, to avoid a verbose function, the input
    will be path to JSON file to be parsed, or a dictionary of the same format.
    """
    if isinstance(device_json, str):
        device_json = json.load(open(device_json, "r"))
    if not isinstance(device_json, dict):
        raise ValueError(f"Unknown type [{type(device_json)}] used for initialization")

    # {
    #     "SENAUX_PD1_GPIO": "22",
    #     "SENAUX_PD2_GPIO": "23",
    #     "SENAUX_F1_GPIO": "20",
    #     "SENAUX_F2_GPIO": "21",
    #     "SENAUX_ADC": {
    #         "ADDR": "0x49",
    #         "C1": "10000/0",
    #         "C2": "10000/0",
    #         "C2": "10000/0",
    #     },
    # }
    def add_gpio_dev(s, dev_name):
        assert s in device_json
        if "DUMMY" in s:
            setattr(hw, dev_name, None)
        else:
            setattr(hw, dev_name, gpio(int(device_json[s]), gpio.READ_WRITE))

    add_gpio_dev("SENAUX_PD1_GPIO", "senaux_pd1_gpio")
    add_gpio_dev("SENAUX_PD2_GPIO", "senaux_pd2_gpio")
    add_gpio_dev("SENAUX_F1_GPIO", "senaux_f1_gpio")
    add_gpio_dev("SENAUX_F2_GPIO", "senaux_f2_gpio")

    assert "SENAUX_ADC" in device_json
    adc_setting = device_json["SENAUX_ADC"]
    if "DUMMY" in adc_setting["ADDR"]:
        hw.senaux_adc = None
    else:
        hw.senaux_adc = i2c_ads1115(1, int(adc_setting["ADDR"], base=16))

    def resisitor_entry(s, dev_name):
        assert s in adc_setting
        assert len(adc_setting[s]) == 2
        setattr(hw, dev_name, adc_setting[s])

    resisitor_entry("C1", "senaux_adc_r1")
    resisitor_entry("C2", "senaux_adc_r2")
    resisitor_entry("C3", "senaux_adc_r3")


def _write_gpio(dev: Union[bool, gpio], val: bool):
    if isinstance(dev, gpio):
        dev.slow_write(val)
    else:
        dev = val
    return dev


def _stat_gpio(dev: Union[bool, gpio]) -> bool:
    if isinstance(dev, gpio):
        return dev.read()
    else:
        return dev


def senaux_enable_pd1(log: logging.Logger, hw: HWContainer):
    hw.senaux_pd1_gpio = _write_gpio(hw.senaux_pd1_gpio, True)


def senaux_disable_pd1(log: logging.Logger, hw: HWContainer):
    hw.senaux_pd1_gpio = _write_gpio(hw.senaux_pd1_gpio, False)


def senaux_status_pd1(log: logging.Logger, hw: HWContainer) -> bool:
    return _stat_gpio(hw.senaux_pd1_gpio)


def senaux_enable_pd2(log: logging.Logger, hw: HWContainer):
    hw.senaux_pd2_gpio = _write_gpio(hw.senaux_pd2_gpio, True)


def senaux_disable_pd2(log: logging.Logger, hw: HWContainer):
    hw.senaux_pd2_gpio = _write_gpio(hw.senaux_pd2_gpio, False)


def senaux_status_pd2(log: logging.Logger, hw: HWContainer) -> bool:
    return _stat_gpio(hw.senaux_pd2_gpio)


def _pulse_gpio(dev, n, wait):
    if isinstance(dev, dev):
        dev.pulse(n=n, wait=wait)


def senaux_pulse_f1(log: logging.Logger, hw: HWContainer, n: int, w: int):
    _pulse_gpio(hw.senaux_pulse_f1, n, w)


def senaux_pulse_f2(log: logging.Logger, hw: HWContainer, n: int, w: int):
    _pulse_gpio(hw.senaux_pulse_f2, n, w)


def senaux_adc_readmv(log: logging.Logger, hw: HWContainer, channel: int) -> float:
    assert 0 <= channel <= 3
    if isinstance(hw.senaux_adc, i2c_ads1115):
        return hw.senaux_adc.read_mv(channel, i2c_ads1115.ADS_RANGE_6V)
    else:
        return numpy.random.normal(2500, 300 * channel)


def senaux_adc_biasresistor(
    log: logging.Logger, hw: HWContainer, channel: int
) -> Tuple[float, float]:
    assert 1 <= channel <= 3
    return getattr(hw, "senaux_adc_r" + str(channel))


_senaux_telemetry_cmds_ = {
    "senaux_status_pd1": senaux_status_pd1,
    "senaux_status_pd2": senaux_status_pd2,
    "senaux_adc_readmv": senaux_adc_readmv,
    "senaux_adc_biasresistor": senaux_adc_biasresistor,
}

_senaux_operation_cmds_ = {
    "reset_senaux_devices": reset_senaux_devices,
    "senaux_enable_pd1": senaux_enable_pd1,
    "senaux_disable_pd1": senaux_disable_pd1,
    "senaux_enable_pd2": senaux_enable_pd2,
    "senaux_disable_pd2": senaux_disable_pd2,
    "senaux_pulse_f1": senaux_pulse_f1,
    "senaux_pulse_f2": senaux_pulse_f2,
}

if __name__ == "__main__":
    import argparse

    from zmq_server import HWControlServer, make_zmq_server_socket

    parser = argparse.ArgumentParser("SenAUX_Testing")
    parser.add_argument("device_json", type=str, nargs=1, help="Path to device json")
    args = parser.parse_args()

    # Declaring a dummy device
    hw = HWContainer()

    # Declaring logging to keep everything by default
    logging.root.setLevel(logging.NOTSET)
    logging.basicConfig(level=logging.NOTSET)

    # Creating the server instance
    server = HWControlServer(
        make_zmq_server_socket(8989),
        logger=logging.getLogger("TestSenAUXMethods"),
        hw=hw,
        telemetry_cmds=_senaux_telemetry_cmds_,
        operation_cmds=_senaux_operation_cmds_,
    )
    reset_senaux_devices(server.logger, server.hw, args.device_json[0])

    # Running the server
    server.run_server()
