from . import version

# Checking version
__version__ = version.__version__

import sys

if sys.version_info.major < 3:
    import warnings

    warnings.warn("Only supports python3!")

# Loading all the various methods
from . import (HVLV_methods, SenAUX_methods, camera_methods, drs_methods,
               gcoder_methods)
from .zmq_client import HWControlClient


# Function for creating the default client with all method loaded
def create_default_client(host: str = "localhost", port: int = 8989):
    # Loading all methods define in the various modules
    camera_methods.register_method_for_client(HWControlClient)
    gcoder_methods.register_method_for_client(HWControlClient)
    drs_methods.register_method_for_client(HWControlClient)
    HVLV_methods.register_method_for_client(HWControlClient)
    SenAUX_methods.register_method_for_client(HWControlClient)

    return HWControlClient(host, port)
