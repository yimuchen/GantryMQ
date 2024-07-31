import sys

if sys.version_info.major < 3:
    import warnings

    warnings.warn("Only supports python3!")

import logging

from camera_methods import CameraDevice
from drs_methods import DRSDevice
from gcoder_methods import GCoderDevice
from HVLV_methods import HVLVDevice
from rigol_methods import RigolPS
from SenAUX_methods import SenAUXDevice

# Loading all the various methods
from zmq_server import (
    HWControlServer,
    make_cmd_parser,
    make_zmq_server_socket,
    parse_cmd_args,
)

if __name__ == "__main__":
    parser = make_cmd_parser(
        "run_server.py",
        """
        Starting the ZMQ server to receive server control requests. While all
        hardware interfaces other than the ZMQ server port can be configured
        client side. It is recommended that you provide a JSON file to start
        the gantry functionality.
        """,
    )
    config = parse_cmd_args(parser)

    # Creating Objects required for server session
    socket = make_zmq_server_socket(port=config["port"])
    logger = logging.getLogger("gmqserver@default")

    server = HWControlServer(
        socket=socket,
        logger=logger,
        hw_list=[
            CameraDevice("camera", logger),
            DRSDevice("drs", logger),
            HVLVDevice("hvlv", logger),
            GCoderDevice("gcoder", logger),
            SenAUXDevice("senaux", logger),
            RigolPS("rigol", logger),
        ],
    )

    # Initializing interfaces defined in the configurations file
    # Loading objects if they are defined in the JSON
    for hw_device in server.hw_list:
        try:
            print(f"Initializing the {hw_device.name}|{type(hw_device)} interfaces...")
            hw_device.reset_devices(config)
        except Exception as err:
            print(
                f"Failed to initialize [{hw_device.name}|{type(hw_device)}]. Client may need to reconfigure {hw_device.name} interfaces"
            )
            print(">>> Original Error:", type(err), err)

    print("Starting the server!!!")
    server.run_server()
