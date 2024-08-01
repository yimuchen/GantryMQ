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
