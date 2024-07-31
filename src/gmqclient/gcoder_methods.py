# Direct methods to be overloaded onto the client
import logging
import time
from typing import Any, Dict, Tuple

from .zmq_client import HWClientInstance


class GCoderDevice(HWClientInstance):
    def __init__(self, name: str):
        super().__init__(name)

    # Simple-wrapped Telemetry methods
    def get_coord(self) -> Tuple[float, float, float]:
        return self._wrap_method()

    def get_current_coord(self) -> Tuple[float, float, float]:
        return self._wrap_method()

    def get_speed(self) -> Tuple[float, float, float]:
        return self._wrap_method()

    def get_settings(self) -> str:
        return self._wrap_method()

    def in_motion(self) -> bool:
        return self._wrap_method()

    # Simple wrapped operation methods
    def reset_devices(self, config: Dict[str, Any]):
        return self._wrap_method(config)

    def run_gcoder(self, cmd: str) -> str:
        return self._wrap_method(cmd)

    def enable_stepper(self, x: bool, y: bool, z: bool):
        return self._wrap_method(x, y, z)

    def disable_stepper(self, x: bool, y: bool, z: bool):
        return self._wrap_method(x, y, z)

    def send_home(self, x: bool, y: bool, z: bool):
        return self._wrap_method(x, y, z)

    def set_speed_limit(self, x: float, y: float, z: float):
        return self._wrap_method(x, y, z)

    # Wrapped method for move_to
    def _raw_move_to_(self, x: float, y: float, z: float):
        return self.client.run_function(
            hw_name=self.name, function_name="move_to", x=x, y=y, z=z
        )

    def move_to(self, x: float, y: float, z: float):
        self._raw_move_to_(x, y, z)
        while self.in_motion():
            time.sleep(0.01)


if __name__ == "__main__":
    import argparse

    from zmq_client import HWControlClient

    parser = argparse.ArgumentParser(
        "gcoder_methods.py", "Simple test program to for interacting with gcoder device"
    )
    parser.add_argument(
        "--serverip", type=str, required=True, help="IP of device controlling printer"
    )
    parser.add_argument(
        "--serverport", type=int, default=8989, help="IP of device controlling printer"
    )
    parser.add_argument(
        "--devpath", type=str, default="/dev/ttyUSB0", help="device path at server"
    )
    args = parser.parse_args()

    # Adding the additional methods

    logging.root.setLevel(1)
    logging.basicConfig(level=logging.NOTSET)
    client = HWControlClient(args.serverip, args.serverport)

    # Testing the gantry controls
    client.claim_operator()
    # client.reset_gcoder_device(args.devpath)
    print(client.get_coord())
    # client.send_home(x=True, y=True, z=True)
    print(client.get_coord())
    client.move_to(x=11, y=12, z=13)
    print(client.get_coord())

    client.close()
