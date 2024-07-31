import argparse
import collections
import json
import logging
import pickle
from typing import Any, Dict, List, Optional, Tuple

import zmq


def _collapse_str_(x: str):
    return " ".join(x.split())


def make_zmq_server_socket(port: int) -> zmq.Socket:
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://*:{port}")
    return socket


class MemHandler(logging.Handler):
    """
    Storing logging records in memory using a first-in-first-out scheme, to be
    re-emitted later. We are expecting that the record list is routinely
    monitored and will not be keeping a persistent copy.
    """

    def __init__(self, capacity: int, level: int = logging.NOTSET):
        super().__init__(level=level)
        self.record_list = collections.deque([], maxlen=capacity)

    def emit(self, record):
        """Main method that needs overloading"""
        self.record_list.append(record)


class HWBaseInstance(object):
    """
    Base class for controlling hardware control instances
    """

    def __init__(self, name: str, logger: logging.Logger):
        self.name = name
        self.logger = logger

        for method in self.all_telemetry_methods + self.all_operation_methods:
            assert hasattr(self, method), (
                "Hardware control class ["
                + self.__class__.__name__
                + "] is missing method: "
                + method
            )

    def reset_devices(self, config: Dict[str, Any]):
        """
        Common method for resetting the underlying hardware configuration. This
        method should always be reimplemented in the concrete hardware control
        classes.
        """
        raise NotImplementedError("Should be overloaded by control class")

    def is_initialized(self) -> bool:
        """
        Method for checking if the underlying hardware instance is initialized
        and ready to be used (needs to be overloaded by extneded classes)
        """
        return False

    def is_dummy(self) -> bool:
        """
        Method for checking if the underlying hardware instance is a "dummy"
        instance: the server side interact is allowed to send/receive control
        instructions, but is not actually controlling a hardware instance; it
        either does nothing or respond with a deterministic response.
        """
        return False

    @property
    def telemetry_methods(self) -> List[str]:
        """
        List of methods that are effectively read-only methods, and can be ran
        safely with multiple connected clients.
        """
        return []

    @property
    def operation_methods(self) -> List[str]:
        """
        List of methods that can only be used by a single client. The main
        server class will be in charge ensuring only a single client
        """
        return []

    @property
    def all_telemetry_methods(self) -> List[str]:
        return self.telemetry_methods + ["is_initialized", "is_dummy"]

    @property
    def all_operation_methods(self) -> List[str]:
        return self.operation_methods


class HWControlServer(object):
    """
    The main server instance that parses the hardware control request from the
    client side to functions calls of the various hardware control classes
    instances. This method also centrally handles the logging, to ensure all
    messages that appears server side will be emitted to the client.
    """

    def __init__(
        self,
        socket: zmq.Socket,
        logger: logging.Logger,
        hw_list: List[HWBaseInstance],
    ):
        # Storing the socket instance to be used
        self.socket = socket
        # ID to keep track of which client assumes control
        self._operator_id: Optional[str] = None

        # Storing the logger instance to be used
        self.logger = logger
        self.mem_handle = MemHandler(capacity=1024, level=logging.NOTSET)
        self.logger.addHandler(self.mem_handle)

        # Adding list of hardware instances that will be controlled by the
        # server instance. In the constructore method, we will be checking that
        # all hardware instances has a unique name
        self.hw_list = hw_list

        _check = list(set([x.name for x in self.hw_list]))
        _hw_name = ",".join(
            [x.name + "(" + x.__class__.__name__ + ")" for x in self.hw_list]
        )
        assert len(_check) == len(self.hw_list), "Duplicate hardware name!" + _hw_name

    def run_single_request(
        self,
        client_id: str,
        hw_name: str,
        function_name: str,
        args=Tuple[Any],
        kwargs=Dict[str, Any],
    ) -> None:
        def return_response(ret: Any) -> None:
            self.socket.send(
                pickle.dumps({"messages": self.clear_message(), "return": ret})
            )

        # Handling special functions
        if function_name == "is_operator":
            return return_response(client_id == self._operator_id)
        if function_name == "claim_operator":
            return return_response(
                self.claim_operator(client_id, error_if_claimed=False)
            )
        if function_name == "release_operator":
            return return_response(self.release_operator(client_id))

        # Finding hw_instance to that should be used.
        hw = self.hw_instance(hw_name)

        # Checking the hardware instance is initialized
        assert (
            hw.is_initialized()
        ), f"Hardware <{hw.name}({type(hw)})> is not initialized"
        if function_name in hw.all_telemetry_methods:
            method = getattr(hw, function_name)
            return return_response(method(*args, **kwargs))
        if function_name in hw.all_operation_methods:
            self.claim_operator(client_id, error_if_claimed=True)
            method = getattr(hw, function_name)
            return return_response(method(*args, **kwargs))
        # Returning default if not recognized
        raise RuntimeError(
            f"Function <{function_name}> of hardware <{hw.name}({type(hw)})> not recognized!"
        )

    def run_server(self):
        while True:
            # Always assume that the code can be decoded using method
            request = self.socket.recv()
            try:
                request = pickle.loads(request)
                self.logger.info(request)
                self.run_single_request(**request)
            except KeyboardInterrupt or InterruptedError:
                # Allow keyboard interaction and stop signals to interrupt
                # server operation
                break
            # Additional exceptions that should terminate hardware control??
            except Exception as err:
                # Sending error message back to client
                self.socket.send(
                    pickle.dumps({"messages": self.clear_message(), "exception": err})
                )
            finally:
                pass

    def clear_message(self) -> List[logging.LogRecord]:
        return_list = [x for x in self.mem_handle.record_list]
        self.mem_handle.record_list.clear()
        return return_list

    def claim_operator(self, client_id: str, error_if_claimed: bool = False) -> None:
        """
        Setting client of id_string to be the unquie identifier
        """
        if self._operator_id is None:
            self.logger.info(f"Claiming operation with ID {client_id}")
        elif self._operator_id != client_id:
            if error_if_claimed:
                raise RuntimeError(
                    _collapse_str_(
                        f"""
                        Operator is claimed by [{self._operator_id}], this
                        operator needs to release control or explicitly claimed
                        before the requested function from [{client_id}]can be
                        processed.
                        """
                    )
                )
            else:
                self.logger.warn(
                    _collapse_str_(
                        f"""
                        Claiming operator id from existing client
                        [{self._operator_id}]! This may cause the existing
                        client to misbehave unless reclaimed.
                        """
                    )
                )
        self._operator_id = client_id

    def release_operator(self, client_id: str):
        if self._operator_id is not None and self._operator_id != client_id:
            raise RuntimeError(
                _collapse_str_(
                    f"""
                    Release can only be called by the operator who has claimed
                    this message! Current operator is [{self._operator_id}]
                    """
                )
            )
        else:
            self.logger.info(f"Releasing operator [{client_id}]")
            self._operator_id = None

    def hw_instance(self, hw_name: str):
        for x in self.hw_list:
            if x.name == hw_name:
                return x
        raise RuntimeError(f"Hardware instance [{hw_name}] is not found")


def make_cmd_parser(file, desc) -> argparse.ArgumentParser:
    """
    Helper function for creating the common command line parser used for starting servers
    """
    parser = argparse.ArgumentParser(
        file, desc, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "config",
        type=str,
        help="""
        Path to the configuration JSON file. Read documentation at:
        https://github.com/UMDCMS/GantryMQ/blob/master/doc/config_server.md For
        more information.
        """,
    )
    return parser


def parse_cmd_args(parser) -> Dict[str, Any]:
    """
    Running the default argument parsing: checking that the configuration file
    is a legal file with the port configuration.
    """
    args = parser.parse_args()
    config = json.load(open(args.config, "r"))

    # Checking the hard requirements
    assert "port" in config, "Configuration [port] was not found in configuration"
    assert isinstance(config["port"], int), "Configuration [port] was not of type int"
    return config


if __name__ == "__main__":
    # Declaring the device container
    parser = make_cmd_parser(
        "zmq_server.py",
        "Spinning a dummy server to check ZMQ server functionality",
    )
    config = parse_cmd_args(parser)

    class DummyHW(HWBaseInstance):
        def __init__(self, name):
            super().__init__(name)
            self.counter = 0

        def check_counter(self, logger: logging.Logger):
            logger.info(self.name + "-" + str(self.counter))
            return self.counter

        def add_counter(self, logger: logging.Logger):
            self.counter = self.counter + 1
            logger.info(self.name + "-" + str(self.counter))

        def is_initialized(self):
            return True

        @property
        def telemetry_methods(self):
            return ["check_counter"]

        @property
        def operation_methods(self):
            return ["add_counter"]

    # Declaring a dummy device

    # Declaring logging to keep everything by default
    logging.root.setLevel(logging.NOTSET)
    logging.basicConfig(level=logging.NOTSET)

    # Creating the server instance
    server = HWControlServer(
        socket=make_zmq_server_socket(config["port"]),
        logger=logging.getLogger("TestServer"),
        hw_list=[DummyHW("dummy")],
    )

    # Running the server
    server.run_server()
