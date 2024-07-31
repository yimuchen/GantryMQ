import logging
import os
from typing import Any, Dict, List, Optional

import numpy

if "GMQPACKAGE_IS_CLIENT" not in os.environ:
    from zmq_server import HWBaseInstance

    from modules.drs import drs
else:
    from gmqclient.server.zmq_server import HWBaseInstance

    drs = None  # Adding a dummy global variable


class DRSDevice(HWBaseInstance):
    def __init__(self, name: str, logger: logging.Logger):
        super().__init__(name, logger)
        self.device: Optional[drs] = None

    def is_initialized(self):
        if self.device is None:
            return False
        return self.device.is_available()

    def reset_devices(self, config: Dict[str, Any]):
        """
        Resetting the DRS device. Loading up the official interface if a
        drs_enable flat is set to true.
        """
        # Close everything
        del self.device
        self.device = None

        # Opening the device if set in the configurations
        if ("drs_enable" in config) and config["drs_enable"]:
            self.device = drs()

    # Most items are simple passthrough methods to the underlying C++ methods

    # Operational methods

    def set_trigger(self, channel: int, level: float, direction: int, delay: float):
        """
        Configuring the trigger for the next data collection routine,
        including:
            - channel | int: channel to use for trigger. Use 4 for external
              trigger
            - level | float: trigger threshold in mV. Ignored for external
              trigger
            - direction | int: trigger direction. 0: raising, 1: falling, 2:
                bidrection. Ignored for external trigger
            - delay | float: trigger delay. Units in ns.
        """
        return self.device.set_trigger(channel, level, direction, delay)

    def set_rate(self, rate: float):
        """Setting the ADC convertion rate. Units in GHz."""
        return self.device.set_rate(rate)

    def set_samples(self, n: int):
        """Setting the number of ADC to collect per waveform"""
        return self.device.set_samples(n)

    def start_collection(self):
        """
        Collecting a buffer given the current trigger settings. Notice this
        will not return the data buffer, use `get_samples` for that.
        """
        return self.device.start_collection()

    def force_stop(self):
        """Stopping the currenct data collection routine"""
        return self.device.force_stop()

    def run_calibration(self):
        """
        Running the DRS internal calibration routine. Because it is impossible
        to know the hardware configuration in software, we assume that the
        hardware is properly configured, as in all ports other than the USB is
        left floating, for calibration.
        """
        return self.device.run_calibration()

    @property
    def operation_methods(self):
        return [
            "reset_devices",
            "set_trigger",
            "set_samples",
            "set_rate",
            "start_collection",
            "force_stop",
            "run_calibration",
        ]

    # Telemetry methods
    def get_time_slice(self) -> numpy.ndarray:
        """Getting the time segmentations of the digitization methods"""
        return self.device.get_time_slice()

    def get_waveform(self) -> numpy.ndarray:
        """Getting the current stored buffer"""
        return self.device.get_waveform()

    def get_trigger_channel(self) -> int:
        """Getting the trigger channel"""
        return self.device.get_trigger_channel()

    def get_trigger_direction(self) -> int:
        """Getting the trigger direction (if using readout channel)"""
        return self.device.get_trigger_direction()

    def get_trigger_level(self) -> float:
        """Getting the trigger level (if using readout channel)"""
        return self.device.get_trigger_level()

    def get_trigger_delay(self) -> float:
        """Getting the trigger delay. Units in ns"""
        return self.device.get_trigger_delay()

    def get_samples(self) -> int:
        """Getting the number of ADCs to collect per waveform"""
        return self.device.get_samples()

    def get_rate(self) -> float:
        """Getting the average sampling rate of the ADC process. Units in GHz"""
        return self.device.get_rate()

    def is_ready(self) -> bool:
        """Is the device ready for starting a set of data collection"""
        return self.device.is_ready()

    @property
    def telemetry_method(self) -> List[str]:
        return [
            "get_time_slice",
            "get_wavefrom",
            "get_trigger_channel",
            "get_trigger_direction",
            "get_trigger_level",
            "get_Trigger_delay",
            "get_samples",
            "get_rate",
            "is_ready",
        ]


if __name__ == "__main__":
    from zmq_server import (
        HWControlServer,
        make_cmd_parser,
        make_zmq_server_socket,
        parse_cmd_args,
    )

    parser = make_cmd_parser("camera_methods.py", "Test server for DRS operations")
    config = parse_cmd_args(parser)

    # Declaring logging to keep everything by default
    logging.root.setLevel(logging.NOTSET)
    logging.basicConfig(level=logging.NOTSET)
    logger = logging.getLogger("TestCameraMethod")

    # Creating the server instance
    server = HWControlServer(
        socket=make_zmq_server_socket(config["port"]),
        logger=logger,
        hw=HWContainer(),
    )

    # Running the server
    server.run_server()
