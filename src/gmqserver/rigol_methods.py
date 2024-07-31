import fcntl
import logging
import os
import time
from typing import Any, Dict, Optional

import pyvisa
import usb.core

if "GMQPACKAGE_IS_CLIENT" not in os.environ:
    from zmq_server import HWBaseInstance

else:
    from gmqclient.server.zmq_server import HWBaseInstance


class RigolPS(HWBaseInstance):
    """
    Pure python object used for interacting with Rigol power supply over USB
    """

    def __init__(self, name: str, logger: logging.Logger):
        super().__init__(name, logger)
        self.device: Optional[pyvisa.resources.Resource] = None
        self.serial: str = "DP8G2318000"  # What did this number come from??
        self.vid: Optional[int] = None  # Vendor ID
        self.pid: Optional[int] = None  # Product ID

    def is_initialized(self):
        return self.device is not None

    def reset_devices(self, config: Dict[str, Any]):
        """Setting the USB device if the "rigo_enable" flag is set to true"""
        # Closing everything
        if self.is_initialized():
            self.device.close()
            self.device = None
            self.vid = None
            self.did = None

        if "rigol_enable" in config and config["rigol_enable"]:
            self.__connect_usb()

    def __connect_usb(self):
        """Connecting the"""
        rm = pyvisa.ResourceManager("@py")
        for res_str in rm.list_resources():
            _iface, _vid, _pid, _serial, _idx, _man = res_str.split("::")
            if self.serial in _serial:
                self.device = rm.open_resource(res_str)
                self.vid = int(_vid, 10)
                self.pid = int(_pid, 10)
                time.sleep(0.1)
                break
        if self.device is None:
            raise RuntimeError("Error, valid VISA address not found")

    def __reset_usb(self):
        """
        Solution to PipeError
        https://github.com/pyvisa/pyvisa-py/issues/72
        https://gist.github.com/PaulFurtado/fce98aef890469f34d51
        """
        USBDEVFS_RESET = ord("U") << (4 * 2) | 20

        xdev = usb.core.find(idVendor=self.vid, idProduct=self.pid)
        dev_path = "/dev/bus/usb/{b:03d}/{a:03d}".format(b=xdev.bus, a=xdev.address)
        fd = os.open(dev_path, os.O_WRONLY)
        try:
            fcntl.ioctl(fd, USBDEVFS_RESET, 0)
            time.sleep(0.1)
        finally:
            os.close(fd)

        self.__connect_usb()  # Is this needed

    def _write(self, msg):
        """Thin wrapper for write operation, reset connection if failed"""
        try:
            self.device.write(msg)
        except ValueError:
            self.__reset_usb()
            return self._write(msg)

    def _query(self, msg):
        """Thing wrapper for read operation, resetting connection if failed"""
        try:
            return self.device.query(msg)
        except ValueError:
            self.__reset_usb()
            return self._query(msg)

    def set_voltage(self, channel: int, value: float):
        """Setting the volage value of specific channel, unit in V"""
        assert channel == 1 or channel == 2, "Channel can only be 1 or 2"
        if channel == 1:
            assert 0 <= value <= 60, "voltage value can only be 0-60"
        if channel == 2:
            assert 0 <= value <= 8, "voltage value can only be 0-8"

        self._write(":APPL CH{c},{v},1".format(c=channel, v=value))
        q = self._query(":APPL? CH{c}".format(c=channel))
        q_v = q.split(",")
        assert len(q_v) == 3, f"Voltage was set incorrectly [{q}]"
        assert float(q_v[1]) == value, f"Voltage mismatch (target: {value}, got: {q})"
        self._write("OUTP CH{c}, ON".format(c=channel))

    def get_voltage(self, channel: int) -> float:
        """Getting the voltage of a channel"""
        assert channel == 1 or channel == 2, "Channel can only be 1 or 2"
        reading = self._query(":MEAS:ALL? CH{c}".format(c=channel))[:-1].split(",")
        return float(reading[0])

    def reset(self):
        """Performing a soft reset of voltage values, no device connection will be reset"""
        self._write("*RST")

    """
    Aliasing channel names
    """

    def set_sipm(self, value: float):
        """Setting SiPM bias voltage (assuming channel 1). Units in V"""
        self.set_voltage(1, value)

    def get_sipm(self) -> float:
        """Getting SiPM bias voltage (assuming channel 1). Units in V"""
        return self.get_voltage(1)

    def set_tb_led(self, value: float):
        """Setting tileboard LED powering voltage (assuming channel 2). Units in V"""
        self.set_voltage(2, value)

    def get_tb_led(self) -> float:
        """Getting tileboard LED powering voltage (assuming channel 2). Units in V"""
        return self.get_voltage(2)


if __name__ == "__main__":
    from zmq_server import (
        HWControlServer,
        make_cmd_parser,
        make_zmq_server_socket,
        parse_cmd_args,
    )

    parser = make_cmd_parser(__file__, "Test server for rigol operations")
    config = parse_cmd_args(parser)

    # Setting logger to log everything
    logging.root.setLevel(logging.NOTSET)
    logging.basicConfig(level=logging.NOTSET)
    logger = logging.getLogger("TestRigolMethods")

    rigol = RigolPS("rigol", logger)
    rigol.reset_devices(config)

    # Creating the server instance
    server = HWControlServer(
        make_zmq_server_socket(config["port"]),
        logger=logger,
        hw_list=[rigol],
    )

    # Running the server
    server.run_server()
