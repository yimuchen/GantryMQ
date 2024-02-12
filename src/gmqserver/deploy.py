import sys

if sys.version_info.major < 3:
    import warnings

    warnings.warn("Only supports python3!")

import logging

import camera_methods
import drs_methods
import gcoder_methods
import HVLV_methods
import rigol_methods
import SenAUX_methods
# Loading all the various methods
from zmq_server import HWContainer, HWControlServer, make_zmq_server_socket

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        "deploy.py",
        "Setting up server with the required hardware",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--port", type=int, default=8989, help="Port to run the server on"
    )
    parser.add_argument(
        "--camera_device",
        type=str,
        default="/dev/video0",
        help="Path to camera device to use, set to empty to disable",
    )
    parser.add_argument(
        "--gcoder_device",
        type=str,
        default="/dev/ttyUSB0",
        help="Path to the USB device that accepts gcoder instructions, set to empty to disable.",
    )
    parser.add_argument(
        "--drs",
        action="store_true",
        help="Whether or not to initialize a DRS readout setting",
    )
    parser.add_argument(
        "--HVLV_json",
        type=str,
        help="Path to HVLV board configuration json file, leave blank to ignore",
    )
    parser.add_argument(
        "--SenAUX_json",
        type=str,
        help="Path to SenAUX board configuration json file, leave blank to ignore",
    )
    args = parser.parse_args()

    # Objects required for server session
    logger = logging.getLogger("gmqserver@default")
    hw = HWContainer
    _telemetry_cmds_ = {}
    _operation_cmds_ = {}

    if args.camera_device:
        camera_methods.reset_camera_device(logger, hw, dev_path=args.camera_device)
    if args.gcoder_device:
        gcoder_methods.reset_gcoder_device(logger, hw, dev_path=args.gcoder_device)
    if args.drs:
        drs_methods.reset_drs_device(logger, hw)
    if args.HVLV_json:
        HVLV_methods.reset_hvlv_devices(logger, hw, args.HVLV_json)
    if args.SenAUX_json:
        SenAUX_methods.reset_senaux_devices(logger, hw, args.SenAUX_json)

    server = HWControlServer(
        make_zmq_server_socket(port=args.port),
        logger=logging.getLogger("gmqserver@default"),
        hw=hw,
        telemetry_cmds={
            **camera_methods._camera_telemetry_cmds_,
            **gcoder_methods._gcoder_telemetry_cmds_,
            **drs_methods._drs_telemetry_cmds_,
            **HVLV_methods._hvlv_telemetry_cmds_,
            **SenAUX_methods._senaux_telemetry_cmds_,
        },
        operation_cmds={
            **camera_methods._camera_operation_cmds_,
            **gcoder_methods._gcoder_operation_cmds_,
            **drs_methods._drs_operation_cmds_,
            **HVLV_methods._hvlv_operation_cmds_,
            **SenAUX_methods._senaux_operation_cmds_,
        },
    )
    print("Starting the server!!!")
    server.run_server()
