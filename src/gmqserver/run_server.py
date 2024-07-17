import sys

if sys.version_info.major < 3:
    import warnings

    warnings.warn("Only supports python3!")

import json
import logging

import src.gmqserver.camera_methods as camera_methods
import src.gmqserver.drs_methods as drs_methods
import src.gmqserver.gcoder_methods as gcoder_methods
import src.gmqserver.HVLV_methods as HVLV_methods
import src.gmqserver.rigol_methods as rigol_methods
import src.gmqserver.SenAUX_methods as SenAUX_methods

# Loading all the various methods
from src.gmqserver.zmq_server import (
    HWContainer,
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
    logger = logging.getLogger("gmqserver@default")
    hw = HWContainer
    _telemetry_cmds_ = {}
    _operation_cmds_ = {}

    server = HWControlServer(
        make_zmq_server_socket(port=config["port"]),
        logger=logging.getLogger("gmqserver@default"),
        hw=hw,
        telemetry_cmds={
            **camera_methods._camera_telemetry_cmds_,
            **gcoder_methods._gcoder_telemetry_cmds_,
            **drs_methods._drs_telemetry_cmds_,
            **HVLV_methods._hvlv_telemetry_cmds_,
            **SenAUX_methods._senaux_telemetry_cmds_,
            **rigol_methods._rigol_telemetry_cmds_,
        },
        operation_cmds={
            **camera_methods._camera_operation_cmds_,
            **gcoder_methods._gcoder_operation_cmds_,
            **drs_methods._drs_operation_cmds_,
            **HVLV_methods._hvlv_operation_cmds_,
            **SenAUX_methods._senaux_operation_cmds_,
            **rigol_methods._rigol_operation_cmds_,
        },
    )

    # Initializing interfaces defined in the configurations file
    # Loading objects if they are defined in the JSON
    for mod, iname in [
        (camera_methods, "camera"),
        (gcoder_methods, "gcoder"),
        (HVLV_methods, "HV/LV board devices"),
        (SenAUX_methods, "Sensor auxiliary devices"),
        (drs_methods, "DRS4"),
        (rigol_methods, "Rigol methods"),
    ]:
        try:
            print(f"Initializing the {iname} interfaces...")
            mod.init_by_config(server.logger, server.hw, config)
        except Exception as err:
            print(
                f"Failed to initialize [{iname}]. Client may need to reconfigure {iname} interfaces"
            )
            print(">>> Original Error:", type(err), err)

    print("Starting the server!!!")
    server.run_server()
