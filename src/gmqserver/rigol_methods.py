"""

Controlling a Rigol power supply using pyvisa

"""
import fcntl
import logging
import os
import time

import pyvisa
import usb.core
from zmq_server import HWContainer


class RigolPS(object):
    """
    Pure python object used for interacting with Rigol power supply over USB
    """

    def __init__(self):
        self.device: str = None
        self.serial: str = None
        self.vid: int = None  # Vendor ID
        self.pid: int = None  # Product ID
        self._reinitialize()

    def _reinitialize(self, serial: str = "DP8G2318000"):
        self.device = None
        self.vid = None
        self.did = None
        self.serial = None
        rm = pyvisa.ResourceManager("@py")
        for res_str in rm.list_resources():
            _iface, _vid, _pid, _serial, _idx, _man = res_str.split("::")
            if serial in _serial:
                self.device = rm.open_resource(res_str)
                self.serial = _serial
                self.vid = int(_vid, 10)
                self.pid = int(_pid, 10)
                time.sleep(0.1)
                break
        if self.device is None:
            raise RuntimeError("Error, valid VISA address not found")

    def _write(self, msg):
        """Thin wrapper for write to reset connection"""
        try:
            self.device.write(msg)
        except ValueError:
            self.__reset_usb()
            return self._write(msg)

    def _query(self, msg):
        try:
            return self.device.query(msg)
        except ValueError:
            self.__reset_usb()
            return self._query(msg)

    def __reset_usb(self):
        """
        Solution to PipeError
        https://github.com/pyvisa/pyvisa-py/issues/72
        https://gist.github.com/PaulFurtado/fce98aef890469f34d51
        """
        print("Issue with connection, resetting USB connections")

        USBDEVFS_RESET = ord("U") << (4 * 2) | 20

        xdev = usb.core.find(idVendor=self.vid, idProduct=self.pid)
        dev_path = "/dev/bus/usb/{b:03d}/{a:03d}".format(b=xdev.bus, a=xdev.address)
        fd = os.open(dev_path, os.O_WRONLY)
        try:
            fcntl.ioctl(fd, USBDEVFS_RESET, 0)
            time.sleep(0.1)
        finally:
            os.close(fd)

        self._reinitialize(self.serial)  # Is this needed

    def set_voltage(self, channel: int, value: float):
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
        assert channel == 1 or channel == 2, "Channel can only be 1 or 2"
        reading = self._query(":MEAS:ALL? CH{c}".format(c=channel))[:-1].split(",")
        return float(reading[0])

    def reset(self):
        self._write("*RST")

    """
    Aliasing channel names
    """

    def set_sipm(self, value: float):
        self.set_voltage(1, value)

    def get_sipm(self) -> float:
        return self.get_voltage(1)

    def set_led(self, value: float):
        self.set_voltage(2, value)

    def get_led(self) -> float:
        return self.get_voltage(2)


# Methods for interacting with the the client object


def reset_rigolps_device(logger: logging.Logger, hw: HWContainer):
    hw.rigolps = RigolPS()


def set_rigol_sipm(logger: logging.Logger, hw: HWContainer, value: float):
    hw.rigolps.set_sipm(value)


def set_rigol_led(logger: logging.Logger, hw: HWContainer, value: float):
    hw.rigolps.set_led(value)


def get_rigol_sipm(logger: logging.Logger, hw: HWContainer) -> float:
    return hw.rigolps.get_sipm()


def get_rigol_led(logger: logging.Logger, hw: HWContainer) -> float:
    return hw.rigolps.get_led()


_rigol_telemetry_cmds_ = {
    "get_rigol_sipm": get_rigol_sipm,
    "get_rigol_led": get_rigol_led,
}

_rigol_operation_cmds_ = {
    "reset_rigolps_device": reset_rigolps_device,
    "set_rigol_sipm": set_rigol_sipm,
    "set_rigol_led": set_rigol_led,
}

if __name__ == "__main__":
    from zmq_server import HWControlServer, make_zmq_server_socket

    # Declaring a dummy device
    hw = HWContainer()

    # Declaring logging to keep everything by default
    logging.root.setLevel(logging.NOTSET)
    logging.basicConfig(level=logging.NOTSET)

    # Creating the server instance
    server = HWControlServer(
        make_zmq_server_socket(8989),
        logger=logging.getLogger("TestRigolMethods"),
        hw=hw,
        telemetry_cmds=_rigol_telemetry_cmds_,
        operation_cmds=_rigol_operation_cmds_,
    )
    reset_rigolps_device(server.logger, server.hw)

    # Running the server
    server.run_server()
