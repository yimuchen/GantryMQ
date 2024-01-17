## Direct methods to be overloaded onto the client
from typing import Tuple, Dict, List


# Basic methods for accessing the various methods
def register_method_for_client(cls):
    for method in [
        # Operation methods
        "reset_hvlv_devices",
        "hv_enable",
        "hv_disable",
        "set_hv_control_mv",
        "set_lv_mv",
        # Telemetry methods,
        "get_hv_status",
        "get_hv_mv",
        "get_hv_control_mv",
        "get_lv_mv",
        "get_vdd_mv",
    ]:
        cls.register_client_method(method)


if __name__ == "__main__":
    from zmq_client import HWControlClient
    import argparse
    import logging
    import time

    parser = argparse.ArgumentParser(
        "HVLV_methods.py",
        "Simple test program to for interacting with HV/LV control board",
    )
    parser.add_argument(
        "--serverip", type=str, required=True, help="IP of device controlling printer"
    )
    parser.add_argument(
        "--serverport", type=int, default=8989, help="IP of device controlling printer"
    )
    args = parser.parse_args()

    # Adding the additional methods
    register_method_for_client(HWControlClient)

    logging.root.setLevel(1)
    logging.basicConfig(level=logging.NOTSET)
    client = HWControlClient(args.serverip, args.serverport)

    # Testing the gantry controls
    client.claim_operator()
    client.hv_enable()
    client.set_lv_bias(0.554)
    client.get_lv_mv()
    time.sleep(1)
    client.close()
