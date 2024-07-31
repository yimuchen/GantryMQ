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


if __name__ == "__main__":
    import argparse
    import logging
    import time

    from zmq_client import HWControlClient

    parser = argparse.ArgumentParser(
        "HVLV_methods.py",
        "Simple test program to for interacting with HV/LV control board",
    )
    parser.add_argument(
        "--serverip", type=str, required=True, help="IP of device controlling printer"
    )
    parser.add_argument(
        "--serverport", type=int, default=8989, help="IP of device controlling printer"
    )
    args = parser.parse_args()

    # Adding the additional methods
    register_method_for_client(HWControlClient)

    logging.root.setLevel(1)
    logging.basicConfig(level=logging.NOTSET)
    client = HWControlClient(args.serverip, args.serverport)

    # Testing the gantry controls
    client.claim_operator()
    client.hv_enable()
    client.set_lv_bias(0.554)
    client.get_lv_mv()
    time.sleep(1)
    client.close()
