from . import version

# Checking version
__version__ = version.__version__

import sys
import os

if sys.version_info.major < 3:
    import warnings

    warnings.warn("Only supports python3!")

# Loading all the various methods
from .zmq_client import HWControlClient
from . import camera_methods
from . import gcoder_methods
from . import drs_methods

# from . import pdf


# Function for creating the default client with all method loaded
def create_default_client(host: str = "localhost", port: int = 8989):
    # Loading all methods define in the various modules
    camera_methods.register_method_for_client(zmq_client.HWControlClient)
    gcoder_methods.register_method_for_client(zmq_client.HWControlClient)
    drs_methods.register_method_for_client(zmq_client.HWControlClient)

    client = zmq_client.HWControlClient(host, port)
