import logging
from typing import Any, Dict

from zmq_server import HWContainer

from modules.drs import drs


def reset_drs_device(logger: logging.Logger, hw: HWContainer):
    """Resetting the DRS device"""
    if not hasattr(hw, "drs_device"):
        hw.drs_device = None

    hw.drs_device = drs()


def create_drs_passthrough(method_name: str) -> None:
    """Passing through the drs methods"""

    def __passthrough_call__(logger, hw, *args, **kwargs):
        return getattr(hw.drs_device, method_name)(*args, **kwargs)

    return __passthrough_call__


_drs_operation_cmds_ = {}
_drs_operation_cmds_.update(
    {
        "drs_" + method_name: create_drs_passthrough(method_name)
        for method_name in [
            "force_stop",
            "start_collection",
            "run_calibration",
            "set_trigger",
            "set_samples",
            "set_rate",
        ]
    }
)
_drs_operation_cmds_.update(
    {
        "reset_drs_device": reset_drs_device,
    }
)

_drs_telemetry_cmds_ = {}
_drs_telemetry_cmds_.update(
    {
        "drs_" + method_name: create_drs_passthrough(method_name)
        for method_name in [
            "get_time_slice",
            "get_waveform",
            "get_trigger_channel",
            "get_trigger_direction",
            "get_trigger_level",
            "get_trigger_delay",
            "get_samples",
            "get_rate",
            "is_available",
            "is_ready",
        ]
    }
)


def init_by_config(logger: logging.Logger, hw: HWContainer, config: Dict[str, Any]):
    if ("drs_enable" in config) and config["drs_enable"]:
        reset_drs_device(logger, hw)


if __name__ == "__main__":
    from zmq_server import (
        HWControlServer,
        make_cmd_parser,
        make_zmq_server_socket,
        parse_cmd_args,
    )

    parser = make_cmd_parser("camera_methods.py", "Test server for DRS operations")
    config = parse_cmd_args(parser)

    # Declaring logging to keep everything by default
    logging.root.setLevel(logging.NOTSET)
    logging.basicConfig(level=logging.NOTSET)

    # Creating the server instance
    server = HWControlServer(
        make_zmq_server_socket(config["port"]),
        logger=logging.getLogger("TestCameraMethod"),
        hw=HWContainer(),
        telemetry_cmds=_drs_telemetry_cmds_,
        operation_cmds=_drs_operation_cmds_,
    )
    init_by_config(server.logger, server.hw, config)

    # Running the server
    server.run_server()
