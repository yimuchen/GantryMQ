import logging
from typing import Any, Dict

import cv2
import numpy
from zmq_server import HWContainer


class _DummyCamera_(object):
    """Dummy camera method"""

    pass


def reset_camera_device(logger: logging.Logger, hw: HWContainer, dev_path: str):
    if not hasattr(hw, "camera_device"):
        hw.camera_device = None

    if isinstance(hw.camera_device, cv2.VideoCapture):
        hw.camera_device.release()

    # Loading the camera instance into the data set
    if "/dummy" not in dev_path:
        hw.camera_device = cv2.VideoCapture(dev_path)

        # Setting up the capture property
        hw.camera_device.set(cv2.CAP_PROP_FRAME_WIDTH, 1240)
        hw.camera_device.set(cv2.CAP_PROP_FRAME_HEIGHT, 1024)
        hw.camera_device.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Always get latest frame
        hw.camera_device.set(cv2.CAP_PROP_SHARPNESS, 0)  # Disable post processing

    # Loading a dummy camera instance


def get_frame(logger: logging.Logger, hw: HWContainer) -> numpy.ndarray:
    if isinstance(hw.camera_device, cv2.VideoCapture):
        if not hw.camera_device.isOpened():
            raise RuntimeError("Video capture device is not available")
        ret, frame = hw.camera_device.read()
        if not ret:
            raise RuntimeError("Can't receive frame from capture device")
        return frame
    else:
        return numpy.array([])


_camera_telemetry_cmds_ = {"camera_get_frame": get_frame}
_camera_operation_cmds_ = {"reset_camera_device": reset_camera_device}


def init_by_config(logger: logging.Logger, hw: HWContainer, config: Dict[str, Any]):
    if "camera_device" in config:
        reset_camera_device(logger, hw, config["camera_device"])


if __name__ == "__main__":
    from zmq_server import (
        HWControlServer,
        make_cmd_parser,
        make_zmq_server_socket,
        parse_cmd_args,
    )

    parser = make_cmd_parser("camera_methods.py", "Test server for camera operations")
    config = parse_cmd_args(parser)

    # Declaring logging to keep everything by default
    logging.root.setLevel(logging.NOTSET)
    logging.basicConfig(level=logging.NOTSET)

    # Creating the server instance
    server = HWControlServer(
        make_zmq_server_socket(config["port"]),
        logger=logging.getLogger("TestCameraMethod"),
        hw=HWContainer(),
        telemetry_cmds=_camera_telemetry_cmds_,
        operation_cmds=_camera_operation_cmds_,
    )
    init_by_config(server.logger, server.hw, config)

    # Running the server
    server.run_server()
