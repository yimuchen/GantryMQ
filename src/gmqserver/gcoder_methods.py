import logging
import os
from typing import Any, Dict, List, Tuple, Union

if "GMQPACKAGE_IS_CLIENT" not in os.environ:
    from zmq_server import HWBaseInstance

    from modules.gcoder import gcoder
else:
    from gmqclient.server.zmq_server import HWBaseInstance

    gcoder = None


class _DummyGantry_:
    """
    Dummy gantry which allows for testing gantry controls without an actual
    gantry control device attached.
    """

    def __init__(self):
        # Dummy geometries saving variables
        self.opx, self.opy, self.opz = 0.0, 0.0, 0.0
        self.vx, self.vy, self.vz = 0.0, 0.0, 0.0
        self.cx, self.cy, self.cz = 0.0, 0.0, 0.0

    def run_gcode(self, gcode: str) -> str:
        return "Dummy gantry_system, do nothing"

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


"""
Main method allowing interactions with the server instance
"""


class GCoderDevice(HWBaseInstance):
    def __init__(self, name: str, logger: logging.Logger):
        super().__init__(name, logger)
        self.device: Union[_DummyGantry_, gcoder, None] = None

    def is_initialized(self) -> bool:
        return self.device is not None

    def is_dummy(self) -> bool:
        return isinstance(self.device, _DummyGantry_)

    def reset_devices(self, config: Dict[str, Any]):
        # Closing everything
        del self.device
        self.device = None

        assert "gcoder_device" in config
        dev_path: str = config["gcoder_device"]
        if "/dummy" not in dev_path:
            self.device = gcoder(dev_path)
        else:
            self.device = _DummyGantry_()

    # Telemetry methods
    def get_coord(self) -> Tuple[float, float, float]:
        """Getting the target motion coordinate. Units in mm"""
        return self.device.opx, self.device.opy, self.device.opz

    def get_current_coord(self) -> Tuple[float, float, float]:
        """Getting the current coordinate. Units in mm"""
        return self.device.cx, self.device.cy, self.device.cz

    def get_speed(self) -> Tuple[float, float, float]:
        """Getting the motion speed. Units in mm/s"""
        return self.device.vx, self.device.vy, self.device.vz

    def get_settings(self) -> str:
        """Getting the configuration strings"""
        return self.device.get_settings()

    def in_motion(self) -> bool:
        """Checking if the gantry is currently in motion"""
        return self.device.in_motion()

    # Operation methods
    def run_gcode(self, cmd: str) -> str:
        """Running a direct gcoder command"""
        return self.device.run_gcode(cmd)

    def set_speed_limit(self, vx: float, vy: float, vz: float) -> None:
        """Setting the motion speed. Unit speed in mm/s"""
        return self.device.set_speed_limit(vx, vy, vz)

    def move_to(self, x: float, y: float, z: float) -> None:
        """Move to location. Unit in mm"""
        return self.device.move_to(x, y, z)

    def send_home(self, x: bool, y: bool, z: bool) -> None:
        """Moving individual axis back to home positions"""
        return self.send_home(x, y, z)

    def enable_stepper(self, x: bool, y: bool, z: bool) -> None:
        """Enabling the stepper motors for each axis"""
        return self.device.enable_stepper(x, y, z)

    def disable_stepper(self, x: bool, y: bool, z: bool) -> None:
        """Disabling the stepper motors for each axis"""
        return self.device.disable_stepper(x, y, z)

    @property
    def telemetry_methods(self) -> List[str]:
        return [
            "get_coord",
            "get_current_coord",
            "get_speed",
            "get_settings",
            "in_motion",
        ]

    @property
    def operation_methods(self) -> List[str]:
        return [
            "reset_devices",
            "run_gcode",
            "set_speed_limit",
            "move_to",
            "send_home",
            "enable_stepper",
            "disable_stepper",
        ]


if __name__ == "__main__":
    from zmq_server import (
        HWControlServer,
        make_cmd_parser,
        make_zmq_server_socket,
        parse_cmd_args,
    )

    parser = make_cmd_parser("gcoder_methods.py", "Test server for gcode operations")
    config = parse_cmd_args(parser)

    # Declaring logging to keep everything by default
    logging.root.setLevel(logging.NOTSET)
    logging.basicConfig(level=logging.NOTSET)
    logger = logging.getLogger("TestGantryMethods")

    # Creating the server instance
    server = HWControlServer(
        make_zmq_server_socket(8989),
        logger=logger,
        hw_list=[GCoderDevice("gcoder", logger)],
    )
    server.hw_list[0].reset_devices(server.logger, config)

    # Running the server
    server.run_server()
