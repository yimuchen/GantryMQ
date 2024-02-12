import collections
import logging
import pickle
from typing import Dict

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
    @brief Storing logging records in memory using a first-in-first-out scheme,
    to be re-emitted later. Here we are expecting that the record list is
    routinely flushed.
    """

    def __init__(self, capacity, level=logging.NOTSET):
        super().__init__(level=level)
        self.record_list = collections.deque([], maxlen=capacity)

    def emit(self, record):
        """Main method that needs overloading"""
        self.record_list.append(record)


class HWContainer(object):
    """Simple container for various hardware interaction instances"""

    pass


class HWControlServer:
    """
    Server for a remote client to contain to a function.
    """

    def __init__(
        self,
        socket: zmq.Socket,
        logger: logging.Logger,
        # Simple container for all the hw instances that is needed to be used
        # to run the server instance. This allows for a partial server ---
        # servers only hosting some of the hardware capabilities --- to be
        # spawned for testing.
        hw: HWContainer,
        # Dictionary for the exposed function name and the method to call for
        # the for additional method handling. All functions listed under this
        # method should follow the convention:
        #
        # Func_Name(logger, hw, **kwargs).
        #
        # This allows for arbitrary methods to be carried out on the various
        # methods. This allows for the logging of the method.
        telemetry_cmds: Dict = None,
        operation_cmds: Dict = None,
    ):
        # Storing the socket instance to be used
        self.socket = socket

        # Storing the logger instance to be used
        self.logger = logger
        self.mem_handle = MemHandler(capacity=1024, level=logging.NOTSET)
        self.logger.addHandler(self.mem_handle)

        # Checking for hw instance container
        self.hw = hw

        # Checking for the logging
        self.telemetry_cmds = telemetry_cmds
        if telemetry_cmds is None:
            self.telemetry_cmds = {}

        self._operator_id = None  # Additional item for locking
        self.operation_cmds = operation_cmds
        if operation_cmds is None:
            self.operation_cmds = {}

        # Registering the basic test testing methods
        self.telemetry_cmds.update(
            {
                "telemetry_test": self.telemetry_test,
            }
        )
        self.operation_cmds.update(
            {
                "operation_test": self.operation_test,
            }
        )

        # Checking for conflicts?

    def run_server(self):
        while True:
            # Always assume that the code can be decoded using method
            request = self.socket.recv()
            ret = None
            try:
                request = pickle.loads(request)
                client_id = request["client_id"]
                function = request["function_name"]
                args = request["args"]
                kwargs = request["kwargs"]
                self.logger.info(request)

                # Running the registerd functions
                # Special methods that required direct calls to lock server flags:
                if function == "is_operator":
                    ret = client_id == self._operator_id
                elif function == "claim_operator":
                    ret = self.claim_operator(client_id)
                elif function == "release_operator":
                    ret = self.release_operator(client_id)
                elif function in self.telemetry_cmds:
                    ret = self.telemetry_cmds[function](
                        self.logger, self.hw, *args, **kwargs
                    )
                elif function in self.operation_cmds:
                    if self._operator_id is None:
                        self.claim_operator(client_id)

                    if self._operator_id != client_id:
                        raise RuntimeError(
                            _collapse_str_(
                                f"""
                                Operator is claimed by [{self._operator_id}],
                                this operator needs to release control (or
                                explicitly claimed) before the requested
                                function [{function}] can be processed."""
                            )
                        )
                    else:
                        ret = self.operation_cmds[function](
                            self.logger, self.hw, *args, **kwargs
                        )

                else:
                    raise RuntimeError(f"Function <{function}> not recognized!")

                #  Send reply back to client
                self.socket.send(
                    pickle.dumps({"messages": self.clear_message(), "return": ret})
                )

            except KeyboardInterrupt or InterruptedError:
                # Allow keyboard interaction and stop signals to interrupt
                # server operation
                break

            except Exception as err:
                # Sending error message back to client
                self.socket.send(
                    pickle.dumps({"messages": self.clear_message(), "exception": err})
                )
            finally:
                pass

    def clear_message(self) -> None:
        return_list = [x for x in self.mem_handle.record_list]
        self.mem_handle.record_list.clear()
        return return_list

    def claim_operator(self, client_id: str):
        if self._operator_id is None:
            self.logger.info(f"Claiming operation with ID {client_id}")
        elif self._operator_id != client_id:
            self.logger.warn(
                _collapse_str_(
                    f"""
                    Claiming operator id from existing client
                    [{self._operator_id}]! This may cause the existing client
                    to misbehave unless reclaimed.
                    """
                )
            )
        self._operator_id = client_id

    def release_operator(self, client_id):
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
            self._operator_id = None

    def telemetry_test(self, logger, hw, msg):
        self.logger.info("This is a message test")
        assert hasattr(hw, "gantry_device")
        return f"This is a telemetry test! {msg}"

    def operation_test(self, logger, hw, msg):
        return f"This is a operation test! {msg}"


if __name__ == "__main__":
    # Declaring the device container

    hw = HWContainer()
    # Declaring a dummy device
    hw.gantry_device = None

    # Declaring logging to keep everything by default
    logging.root.setLevel(logging.NOTSET)
    logging.basicConfig(level=logging.NOTSET)

    # Creating the server instance
    server = HWControlServer(
        make_zmq_server_socket(8989), logger=logging.getLogger("TestServer"), hw=hw
    )

    # Running the server
    server.run_server()
