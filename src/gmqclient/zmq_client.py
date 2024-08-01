import inspect
import logging
import os
import pickle
from socket import gethostname
from typing import List

import zmq

# hack to have different import behaviors for loading server side descriptions
os.environ["GMQPACKAGE_IS_CLIENT"] = "1"

# Needs to be placed here
from .server.zmq_server import HWBaseInstance


def make_zmq_client_socket(host: str, port: int) -> zmq.Socket:
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(f"tcp://{host}:{port}")
    return socket


def add_serverclass_doc(serverclass):
    """
    Extracting the __doc__ string of the server-side class and setting this as
    the base string. This is to help ensure that the documentation is mirrored.
    For methods where we are directly copying the documentation, we also expect
    the function signature to match as well, and will throw an exception at
    import time if a mismatch is detected
    """

    def decorator(client_method):
        server_method = getattr(serverclass, client_method.__name__)
        client_sig = inspect.signature(client_method)
        server_sig = inspect.signature(server_method)

        # Checking if number of parameters match
        assert len(client_sig.parameters) == len(server_sig.parameters), (
            "Mismatch parameter count:"
            + serverclass.__name__
            + "."
            + client_method.__name__
        )

        # Checking that all parameters have the same signature
        for client_param, server_param in zip(
            client_sig.parameters.values(), server_sig.parameters.values()
        ):
            assert client_param.annotation == server_param.annotation, (
                "Annotation mismatch: "
                + serverclass.__name__
                + "."
                + client_method.__name__
                + " : "
                + server_param.name
            )
        # Checking the return parameter are identical
        assert client_sig.return_annotation == server_sig.return_annotation, (
            "Return data type mismatch:"
            + serverclass.__name__
            + "."
            + client_method.__name__
            + " : "
            + str(server_sig.return_annotation),
        )

        # Returning the modified method
        client_method.__doc__ = server_method.__doc__
        return client_method

    return decorator


class HWClientInstance(object):
    """
    Base class for running a server side methods
    """

    def __init__(self, name: str):
        self.name = name
        self.client: HWControlClient = None

    def _wrap_method(self, *args, **kwargs):
        """
        Helper function for calling a thing wrapper based on the method name in
        the call stack and the defined name of the hardware we wish to control.
        """
        return self.client.run_function(
            self.name,
            inspect.stack()[1][3],
            *args,
            **kwargs,
        )

    """
    Common methods that exists for all hardware control instances
    """

    @add_serverclass_doc(HWBaseInstance)
    def is_initialized(self) -> bool:
        return self._wrap_method()

    @add_serverclass_doc(HWBaseInstance)
    def is_dummy(self) -> bool:
        return self._wrap_method()


class HWControlClient(object):
    def __init__(
        self,
        socket: zmq.Socket,
        logger: logging.Logger,
        hw_list: List[HWClientInstance],
    ):
        self.socket = socket
        self.client_id = f"{gethostname()}@{os.getpid()}"
        self.logger = logger
        # Storing the host/port information for debugging
        self.hw_list = hw_list
        for hw in self.hw_list:
            hw.client = self

    def is_operator(self) -> bool:
        """
        Checking if this client is the operator that is allowed to call
        operation methods
        """
        return self.run_function(hw_name="", function_name="is_operator")

    def claim_operator(self) -> None:
        """Force claiming the use of operation method"""
        return self.run_function(hw_name="", function_name="claim_operator")

    def release_operator(self) -> None:
        """Relinquish the use of operation methods"""
        return self.run_function(hw_name="", function_name="release_operator")

    def close(self):
        """
        Always attempt to release the operator on exit. For methods in the
        destructor, we cannot use the dynamically declared methods.
        """
        print("Running desctuctor")
        if self.is_operator():
            self.release_operator()
        self.socket.close()

    def run_function(self, hw_name: str, function_name: str, *args, **kwargs):
        """
        Running a function on the server side. The function is should be
        uniquely identified by the hardware instance name, and the method used.
        All other arguments will be passed as a collection of iterable *args
        and mapping **kwargs.
        """
        # Sending function inputs
        self.socket.send(
            pickle.dumps(
                dict(
                    client_id=self.client_id,
                    hw_name=hw_name,
                    function_name=function_name,
                    args=args,
                    kwargs=kwargs,
                )
            )
        )

        # Getting raw response
        response = pickle.loads(self.socket.recv())

        # Re-emitting the message information
        for record in response["messages"]:
            self.logger.handle(record)

        # Casting the return type
        if "exception" in response:
            print(
                "Raised form server:",
                response["exception"],
                type(response["exception"]),
            )
            raise response["exception"]
        else:
            return response["return"]


if __name__ == "__main__":
    # Setting up a logger to has everything
    logging.root.setLevel(1)
    logging.basicConfig(level=logging.NOTSET)

    # Creating the dummy instance for the item
    class DummyHW(HWClientInstance):
        def __init__(self, name):
            super().__init__(name)

        def check_counter(self):
            return self._wrap_method()

        def add_counter(self):
            return self._wrap_method()

    client = HWControlClient(
        socket=make_zmq_client_socket("localhost", 8989),
        logger=logging.Logger("TestClient"),
        hw_list=[DummyHW("dummy")],
    )

    for request in range(10):
        print(client.hw_list[0].check_counter())

    try:
        client.hw_list[0].add_counter()
    except Exception:
        print("Ran into error!")
        client.claim_operator()
        client.hw_list[0].add_counter()

    for request in range(10):
        print(client.hw_list[0].check_counter())

    client.close()
