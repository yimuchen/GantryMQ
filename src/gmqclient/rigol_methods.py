from typing import Any, Dict

from .server import rigol_methods as Server
from .zmq_client import HWClientInstance, add_serverclass_doc


class RigolDevice(HWClientInstance):
    def __init__(self, name: str):
        super().__init__(name)

    # All methods are simply pass throughs
    @add_serverclass_doc(Server.RigolPS)
    def reset_devices(self, config: Dict[str, Any]):
        return self._wrap_method(config)

    @add_serverclass_doc(Server.RigolPS)
    def reset(self):
        return self._wrap_method()

    @add_serverclass_doc(Server.RigolPS)
    def set_voltage(self, channel: int, value: float):
        return self._wrap_method(channel, value)

    @add_serverclass_doc(Server.RigolPS)
    def get_voltage(self, channel: int):
        return self._wrap_method(channel)

    @add_serverclass_doc(Server.RigolPS)
    def set_sipm(self, value: float):
        return self._wrap_method(value)

    @add_serverclass_doc(Server.RigolPS)
    def get_sipm(self):
        return self._wrap_method()

    @add_serverclass_doc(Server.RigolPS)
    def set_tb_led(self, value: float):
        return self._wrap_method(value)

    @add_serverclass_doc(Server.RigolPS)
    def get_tb_led(self):
        return self._wrap_method()
