import logging
import os
from typing import Any, Dict, List, Optional

import cv2
import numpy

if "GMQPACKAGE_IS_CLIENT" not in os.environ:
    from zmq_server import HWBaseInstance
else:
    from gmqclient.server.zmq_server import HWBaseInstance


class CameraDevice(HWBaseInstance):
    def __init__(self, name: str, logger: logging.Logger):
        super().__init__(name, logger)
        self.device: Optional[cv2.VideoCapture] = None

    def is_initialized(self):
        return True

    def is_dummy(self):
        return self.device is None

    def reset_devices(self, config: Dict[str, Any]):
        # Closing everything
        if isinstance(self.device, cv2.VideoCapture):
            self.device.release()
            self.device = None

        # Checking the configuration format
        assert self.name + "_device_path" in config
        dev_path = config[self.name + "_device_path"]

        # Loading the camera instance into the data set
        if "/dummy" not in dev_path:
            self.device = cv2.VideoCapture(dev_path)

            # Setting up the capture property
            self.device.set(cv2.CAP_PROP_FRAME_WIDTH, 1240)
            self.device.set(cv2.CAP_PROP_FRAME_HEIGHT, 1024)
            self.device.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Always get latest frame
            self.device.set(cv2.CAP_PROP_SHARPNESS, 0)  # Disable post processing

        # Loading a dummy camera instance

    def get_frame(self) -> numpy.ndarray:
        if isinstance(self.device, cv2.VideoCapture):
            if not self.device.isOpened():
                raise RuntimeError("Video capture device is not available")
            ret, frame = self.device.read()
            if not ret:
                raise RuntimeError("Can't receive frame from capture device")
            return frame
        else:
            return numpy.array([])

    @property
    def telemetry_methods(self) -> List[str]:
        return ["get_frame"]

    @property
    def operation_methods(self) -> List[str]:
        return ["reset_devices"]


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
    logger = logging.getLogger("TestCameraMethod")

    # Creating the server instance
    server = HWControlServer(
        socket=make_zmq_server_socket(config["port"]),
        logger=logger,
        hw=CameraDevice.init_by_config(logger, config),
    )

    # Running the server
    server.run_server()
