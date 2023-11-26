from zmq_server import HWContainer
from modules.drs import drs

import logging
import numpy


def reset_drs_device(logger: logging.Logger, hw: HWContainer):
    """Resetting the DRS device"""
    if not hasattr(hw, drs_device):
        hw.drs_device = None

    hw.drs_device = drs.drs()


def create_drs_passthrough(method_name: str) -> None:
    """Passing through the drs methods"""

    def __passthrough_call__(logger, hw, *args, **kwargs):
        return getattr(hw.drs_device, method_name)(*args, **kwargs)

    return __passthrough_call__


_drs_operation_cmds_ = {}
_drs_operation_cmds_.update(
    {
        method_name: create_drs_passthrough(method_name)
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
        method_name: create_drs_passthrough(method_name)
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
