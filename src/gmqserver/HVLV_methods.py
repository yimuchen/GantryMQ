import json
import logging
from typing import Any, Dict, Union

from zmq_server import HWContainer

from modules.gpio import gpio
from modules.i2c_ads1115 import i2c_ads1115
from modules.i2c_mcp4725 import i2c_mcp4725


def reset_hvlv_devices(
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
    #   "HV_ENABLE_GPIO": "27",
    #   "HVLV_ADC_ADDR": "0x48",
    #   "HV_DAC_ADDR": "0x64",
    #   "LV_DAC_ADDR": "0x65"
    # }

    # First check everything is preset in the configuration
    assert "HV_ENABLE_GPIO" in device_json
    assert "HVLV_ADC_ADDR" in device_json
    assert "HV_DAC_ADDR" in device_json
    assert "LV_DAC_ADDR" in device_json

    hw.hv_gpio = (
        gpio(int(device_json["HV_ENABLE_GPIO"]), gpio.READ_WRITE)
        if "DUMMY" not in device_json["HV_ENABLE_GPIO"]
        else None
    )
    hw.hvlv_adc = (
        i2c_ads1115(1, int(device_json["HVLV_ADC_ADDR"], base=16))
        if "DUMMY" not in device_json["HVLV_ADC_ADDR"]
        else None
    )
    hw.hv_dac = (
        i2c_mcp4725(1, int(device_json["HV_DAC_ADDR"], base=16))
        if "DUMMY" not in device_json["HV_DAC_ADDR"]
        else None
    )
    hw.lv_dac = (
        i2c_mcp4725(1, int(device_json["LV_DAC_ADDR"], base=16))
        if "DUMMY" not in device_json["LV_DAC_ADDR"]
        else None
    )


def hv_enable(logger: logging.Logger, hw: HWContainer):
    if isinstance(hw.hv_gpio, gpio):
        hw.hv_gpio.slow_write(True)
    else:
        hw.hv_gpio = True


def hv_disable(logger: logging.Logger, hw: HWContainer):
    if isinstance(hw.hv_gpio, gpio):
        hw.hv_gpio.slow_write(False)
    else:
        hw.hv_gpio = False


def get_hv_status(logger: logging.Logger, hw: HWContainer) -> bool:
    if isinstance(hw.hv_gpio, gpio):
        return hw.hv_gpio.read()
    else:
        return hw.hv_gpio


def set_hv_control_mv(logger: logging.Logger, hw: HWContainer, target: float):
    # TODO: Handle proper operation of VDD
    assert 0 <= target <= 5000
    vdd = get_vdd_mv(logger, hw)
    if isinstance(hw.hv_dac, i2c_mcp4725):
        hw.hv_dac.set_int(int(4095 * float(target / vdd)))
    else:
        hw.hv_dac = target


def set_lv_mv(logger: logging.Logger, hw: HWContainer, target: float):
    # TODO: Handle proper operation of VDD
    assert 0 <= target <= 5000
    vdd = get_vdd_mv(logger, hw)
    if isinstance(hw.lv_dac, i2c_mcp4725):
        hw.lv_dac.set_int(int(4095 * float(target / vdd)))
    else:
        hw.lv_dac = target


def get_hv_mv(logger: logging.Logger, hw: HWContainer) -> float:
    if isinstance(hw.hvlv_adc, i2c_ads1115):
        # TODO: 101 from multiple divider values. programmable??
        return hw.hvlv_adc.read_mv(0, i2c_ads1115.ADS_RANGE_1V) * 101
    else:
        if get_hv_status(logger, hw):
            # TODO better indirect estimate based on control voltage
            return 70
        else:
            return 0


def get_hv_control_mv(logger: logging.Logger, hw: HWContainer) -> float:
    if isinstance(hw.hvlv_adc, i2c_ads1115):
        return hw.hvlv_adc.read_mv(1, i2c_ads1115.ADS_RANGE_4V)
    else:
        if isinstance(hw.hv_dac, i2c_mcp4725):
            return get_vdd_mv(logger, hw) * hw.hv_dac.read_int() / 4096.0
        else:
            return hw.hv_dac


def get_lv_mv(logger: logging.Logger, hw: HWContainer) -> float:
    # TODO: Cannot read this due to hardware design flaw. Using DAC register
    # value as a work around
    if isinstance(hw.hvlv_adc, i2c_ads1115) and False:
        return hw.hvlv_adc.read_mv(2, i2c_ads1115.ADS_RANGE_4V)
    else:
        if isinstance(hw.lv_dac, i2c_mcp4725):
            return get_vdd_mv(logger, hw) * hw.lv_dac.read_int() / 4096.0
        else:
            return hw.lv_dac


def get_vdd_mv(logger: logging.Logger, hw: HWContainer) -> float:
    if isinstance(hw.hvlv_adc, i2c_ads1115):
        return hw.hvlv_adc.read_mv(3, i2c_ads1115.ADS_RANGE_6V)
    else:
        return 5000


_hvlv_telemetry_cmds_ = {
    "get_hv_status": get_hv_status,
    "get_hv_mv": get_hv_mv,
    "get_hv_control_mv": get_hv_control_mv,
    "get_lv_mv": get_lv_mv,
    "get_vdd_mv": get_vdd_mv,
}

_hvlv_operation_cmds_ = {
    "reset_hvlv_devices": reset_hvlv_devices,
    "hv_enable": hv_enable,
    "hv_disable": hv_disable,
    "set_hv_control_mv": set_hv_control_mv,
    "set_lv_mv": set_lv_mv,
}


def init_by_config(logger: logging.Logger, hw: HWContainer, config: Dict[str, Any]):
    if "HV_ENABLE_GPIO" in config:
        reset_hvlv_devices(logger, hw, config)


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

    # Creating the server instance
    server = HWControlServer(
        make_zmq_server_socket(config["port"]),
        logger=logging.getLogger("TestHVLVMethods"),
        hw=HWContainer(),
        telemetry_cmds=_hvlv_telemetry_cmds_,
        operation_cmds=_hvlv_operation_cmds_,
    )
    init_by_config(server.logger, server.hw, config)

    # Running the server
    server.run_server()
