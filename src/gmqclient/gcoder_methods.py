## Direct methods to be overloaded onto the client
from typing import Tuple, Dict, List

import logging


# Basic methods for accessing the various methods
def register_method_for_client(cls):
    for method in [
        # Operation
        "reset_gcoder_device",
        "run_gcode",
        "set_speed_limit",
        ## "move_to", special method!!
        "enable_stepper",
        "disable_stepper",
        "send_home",
        # Telemetry
        "get_settings",
        "in_motion",
        "get_coord",
        "get_current_coord",
        "get_speed",
    ]:
        cls.register_client_method(method)

    cls.register_client_method("move_to", "_raw_move_to")

    # Improved client-side move to to ensure motion is completed
    def _move_to_(self, x, y, z):
        self._raw_move_to(x=x, y=y, z=z)
        while self.in_motion():
            time.sleep(0.01)

    setattr(cls, "move_to", _move_to_)


if __name__ == "__main__":
    from zmq_client import HWControlClient

    # Adding the additional methods
    register_method_for_client(HWControlClient)

    logging.root.setLevel(1)
    logging.basicConfig(level=logging.NOTSET)
    client = HWControlClient("localhost", 8989)

    # Testing the gantry controls
    client.claim_operator()
    client.reset_gcoder_device("/dev/dummy")
    print(client.get_coord())
    client.send_home(x=True, y=True, z=True)
    print(client.get_coord())
    client.move_to(x=100, y=200, z=200)
    print(client.get_coord())
