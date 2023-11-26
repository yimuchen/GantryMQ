# Do nothing for now
import sys
import os

if sys.version_info.major < 3:
    import warnings

    warnings.warn("Only supports python3!")

# Loading all the various methods
from zmq_server import HWContainer, HWControlServer, make_zmq_server_socket
import camera_methods
import gcoder_methods
import drs_methods

from typing import Optional
import logging


def create_default_devices(**kwargs):
    """Spawning default devices for operating the gantry system"""
    hw = HWContainer
    camera_methods.reset_camera_device(
        None, hw, dev_path=kwargs.get("camera_device", "/dev/video0")
    )
    gcoder_methods.reset_gcoder_device(
        None, hw, dev_path=kwargs.get("gcoder_device", "/dev/ttyUSB0")
    )
    drs_methods.reset_drs_device(None, hw)

    return hw


# Function for creating the default client with all method loaded
def create_default_server(
    hw: HWContainer,
    logger: Optional[logging.Logger] = None,
    port: int = 8989,
):
    """
    Function for creating the default server instance. The hardware container
    will need to be passed in separately
    """
    server = HWControlServer(
        make_zmq_server_socket(port=port),
        logger=logging.getLogger("gmqserver@default"),
        hw=hw,
        telemetry_cmds={
            **camera_methods._camera_telemetry_cmds_,
            **gcoder_methods._gcoder_telemetry_cmds_,
            **drs_methods._drs_telemetry_cmds_,
        },
        operation_cmds={
            **camera_methods._camera_operation_cmds_,
            **gcoder_methods._gcoder_operation_cmds_,
            **drs_methods._drs_operation_cmds_,
        },
    )

    return server


if __name__ == "__main__":
    hw = create_default_devices()
    server = create_default_devices(
        hw=hw, logger=logging.getLogger("gmqserver@default"), port=8989
    )

    server.run_server()
