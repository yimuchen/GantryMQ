import logging

# This must be loaded first
from .zmq_client import HWControlClient, make_zmq_client_socket

# Loading all the various methods
from . import version
from .camera_methods import CameraDevice
from .drs_methods import DRSDevice
from .gcoder_methods import GCoderDevice
from .HVLV_methods import HVLVDevice
from .SenAUX_methods import SenAUXDevice


# Checking version
__version__ = version.__version__


class GMQClient(HWControlClient):
    """Default client that spawns on of each defined interface"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8989,
    ):
        super().__init__(
            socket=make_zmq_client_socket(host, port),
            logger=logging.Logger("gmqclient"),
            hw_list=[
                CameraDevice("camera"),
                DRSDevice("drs"),
                GCoderDevice("gcoder"),
                HVLVDevice("hvlv"),
                SenAUXDevice("senaux"),
            ],
        )

    # Adding aliases to the various hardware clients. Using this syntax as
    # it is nicer for static python analyzer for editors
    @property
    def camera(self) -> CameraDevice:
        return self.hw_list[0]

    @property
    def drs(self) -> DRSDevice:
        return self.hw_list[1]

    @property
    def gcoder(self) -> GCoderDevice:
        return self.hw_list[2]

    @property
    def hvlv(self) -> HVLVDevice:
        return self.hw_list[3]

    @property
    def senaux(self) -> SenAUXDevice:
        return self.hw_list[4]
