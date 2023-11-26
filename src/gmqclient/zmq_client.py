from typing import Optional

import zmq
import json
import os
import logging
import pickle
from socket import gethostname


class HWControlClient:
    def __init__(self, host: str, port: int, logger=None):
        context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        self.socket.connect(f"tcp://{host}:{port}")
        self.client_id = f"{gethostname()}@{os.getpid()}"
        self.logger = logger

        if self.logger is None:  #
            self.logger = logging.getLogger(self.client_id)

        # Allowing methods to appear directly as attributes instead of having to
        # include the `_run_function` everywhere
        HWControlClient.register_client_method("release_operator")
        HWControlClient.register_client_method("claim_operator")
        HWControlClient.register_client_method("is_operator")

    def __del__(self):
        # Always attempt to release the operator on exit. For methods in the
        # destructor, we cannot use the dynamically declared methods (for some
        # reason?)
        if self._run_function("is_operator"):
            self._run_function("release_operator")

    def register_client_method(func_name: str, rename: Optional[str] = None) -> None:
        """
        Creating a dynamic method so that, instead of explicitly calling
        `client._run_function(<func_name>, **kwargs)`, the user can write
        `client.<renamed>(**kwargs)`. If `renamed` is not specified, then the
        renamed is mapped to `func_name`
        """
        if rename is None:
            rename = func_name

        def __inner_call__(self, *args, **kwargs):
            return self._run_function(func_name, *args, **kwargs)

        setattr(HWControlClient, rename, __inner_call__)

    def _run_function(self, func_name, *args, **kwargs):
        # Sending function inputs
        self.socket.send(
            pickle.dumps(
                dict(
                    client_id=self.client_id,
                    function_name=func_name,
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
            print(response["exception"], type(response["exception"]))
            raise response["exception"]
        else:
            return response["return"]


if __name__ == "__main__":
    # Setting up a logger to has everything
    logging.root.setLevel(1)
    logging.basicConfig(level=logging.NOTSET)
    client = HWControlClient("localhost", 8989)

    for request in range(10):
        print(client._run_function("telemetry_test", msg=request**2))

    try:
        client._run_function("operation_test", msg=3)
    except Exception as err:
        print("Ran into error!")
        client.claim_operator()
        client._run_function("operation_test", msg=3)

    # This line should fail regard less
    try:
        print(client._run_function("mytest"))
    except Exception as err:
        print(err)
