# Direct methods to be overloaded onto the client
import logging
import time


# Basic methods for accessing the various methods
def register_method_for_client(cls):
    for method in [
        # Operation
        "reset_gcoder_device",
        "gcoder_run_gcode",
        "gcoder_set_speed_limit",
        # "move_to", special method!! over loaded to something else
        "gcoder_enable_stepper",
        "gcoder_disable_stepper",
        "gcoder_send_home",
        # Telemetry
        "gcoder_get_settings",
        "gcoder_in_motion",
        "gcoder_get_coord",
        "gcoder_get_current_coord",
        "gcoder_get_speed",
    ]:
        cls.register_client_method(method)

    cls.register_client_method("gcoder_move_to", "_gcoder_raw_move_to")

    # Improved client-side move to to ensure motion is completed
    def _move_to_(self, x, y, z):
        self._gcoder_raw_move_to(x=x, y=y, z=z)
        while self.gcoder_in_motion():
            time.sleep(0.01)

    setattr(cls, "gcoder_move_to", _move_to_)


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
    register_method_for_client(HWControlClient)

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
