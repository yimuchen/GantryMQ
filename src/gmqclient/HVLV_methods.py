from typing import Any, Dict, List

from .server import HVLV_methods
from .zmq_client import HWClientInstance, add_serverclass_doc


class HVLVDevice(HWClientInstance):
    def __init__(self, name: str):
        super().__init__(name)

    @add_serverclass_doc(HVLV_methods.HVLVDevice)
    def reset_devices(self, config: Dict[str, Any]):
        return self._wrap_method(config)

    @add_serverclass_doc(HVLV_methods.HVLVDevice)
    def hv_enable(self):
        return self._wrap_method()

    @add_serverclass_doc(HVLV_methods.HVLVDevice)
    def hv_disable(self):
        return self._wrap_method()

    @add_serverclass_doc(HVLV_methods.HVLVDevice)
    def set_hv_control_mv(self, target: float):
        return self._wrap_method(target)

    @add_serverclass_doc(HVLV_methods.HVLVDevice)
    def set_lv_mv(self, target: float):
        return self._wrap_method(target)

    @add_serverclass_doc(HVLV_methods.HVLVDevice)
    def get_hv_status(self) -> bool:
        return self._wrap_method()

    @add_serverclass_doc(HVLV_methods.HVLVDevice)
    def get_hv_mv(self) -> float:
        return self._wrap_method()

    @add_serverclass_doc(HVLV_methods.HVLVDevice)
    def get_hv_control_mv(self) -> float:
        return self._wrap_method()

    @add_serverclass_doc(HVLV_methods.HVLVDevice)
    def get_lv_mv(self) -> float:
        return self._wrap_method()

    @add_serverclass_doc(HVLV_methods.HVLVDevice)
    def get_vdd_mv(self) -> float:
        return self._wrap_method()
