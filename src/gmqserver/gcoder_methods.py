from zmq_server import HWContainer
from modules.gcoder import gcoder

from typing import Tuple, List
import logging


class _DummyGantry_:
    """
    Dummy gantry which allows for testing gantry controls without an actual gantry
    control device attached.
    """

    def __init__(self):
        # Dummy geometries saving variables
        self.opx, self.opy, self.opz = 0.0, 0.0, 0.0
        self.vx, self.vy, self.vz = 0.0, 0.0, 0.0
        self.cx, self.cy, self.cz = 0.0, 0.0, 0.0

    def run_gcode(self, gcode: str) -> str:
        return "Dummy run, do nothing"

    def set_speed_limit(self, x: float, y: float, z: float) -> None:
        self.vx, self.vy, self.vz = x, y, z

    def move_to(self, x: float, y: float, z: float) -> None:
        self.opx, self.opy, self.opz = x, y, z
        self.cx, self.cy, self.cz = x, y, z

    def enable_stepper(self, x: bool, y: bool, z: bool) -> None:
        pass

    def disable_stepper(self, x: bool, y: bool, z: bool) -> None:
        pass

    def send_home(self, x: bool, y: bool, z: bool) -> None:
        if x is True:
            self.opx, self.cx = 0.0, 0.0
        if y is True:
            self.opy, self.cy = 0.0, 0.0
        if z is True:
            self.opz, self.cz = 0.0, 0.0

    def in_motion(self):
        return False

        # Defining functions for gantry operation
        for gantry_method in []:
            GantryServer.register_gantry_passthrough(gantry_method)
            self.register_operation_method(gantry_method)
        # Defining functions for gantry telemetry monitoring
        for gantry_method in [
            "get_settings",
            "in_motion",
        ]:
            GantryServer.register_gantry_passthrough(gantry_method)
            self.register_telemetry_method(gantry_method)
        # Methods for accessing the step only access
        self.register_telemetry_method("get_coord")
        self.register_telemetry_method("get_current_coord")
        self.register_telemetry_method("get_speed")


"""
Methods to be exposed to the gantry methods
"""


def create_gantry_passthrough(method_name: str) -> None:
    """Passing through the gantry device methods"""

    def __passthrough_call__(logger, hw, *args, **kwargs):
        return getattr(hw.gantry_device, method_name)(*args, **kwargs)

    return __passthrough_call__


def reset_gcoder_device(logger, hw, dev_path: str) -> None:
    if "/dummy" not in dev_path:
        hw.gantry_device = gcoder(dev_path)
    else:
        hw.gantry_device = _DummyGantry_()


def get_coord(logger, hw) -> Tuple[float]:
    return hw.gantry_device.opx, hw.gantry_device.opy, hw.gantry_device.opz


def get_current_coord(logger, hw) -> Tuple[float]:
    return hw.gantry_device.cx, hw.gantry_device.cy, hw.gantry_device.cz


def get_speed(logger, hw) -> Tuple[float]:
    return hw.gantry_device.vx, hw.gantry_device.vy, hw.gantry_device.vz


# Pass through methods (see hardware/gcoder.cc pybind modules)
_gcoder_operation_cmds_ = {}
_gcoder_operation_cmds_.update(
    {
        method_name: create_gantry_passthrough(method_name)
        for method_name in [
            "run_gcode",
            "set_speed_limit",
            "move_to",
            "enable_stepper",
            "disable_stepper",
            "send_home",
        ]
    }
)
_gcoder_operation_cmds_.update(
    {
        "reset_gcoder_device": reset_gcoder_device,
    }
)

_gcoder_telemetry_cmds_ = {}
_gcoder_telemetry_cmds_.update(
    {
        method_name: create_gantry_passthrough(method_name)
        for method_name in ["get_settings", "in_motion"]
    }
)
_gcoder_telemetry_cmds_.update(
    {
        "get_coord": get_coord,
        "get_current_coord": get_current_coord,
        "get_speed": get_speed,
    }
)


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
        logger=logging.getLogger("TestGantryMethods"),
        hw=hw,
        telemetry_cmds=_gcoder_telemetry_cmds_,
        operation_cmds=_gcoder_operation_cmds_,
    )

    # Running the server
    server.run_server()
