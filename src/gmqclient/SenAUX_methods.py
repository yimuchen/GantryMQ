from typing import Any, Dict, Tuple

from .server.SenAUX_methods import SenAUXDevice as SenAUXServer
from .zmq_client import HWClientInstance, add_serverclass_doc


class SenAUXDevice(HWClientInstance):
    def __init__(self, name: str):
        super().__init__(name)

    # Operation methods are typically thin passthrough methods
    @add_serverclass_doc(SenAUXServer)
    def reset_devices(self, config: Dict[str, Any]):
        return self._wrap_method(config)

    @add_serverclass_doc(SenAUXServer)
    def enable_pd1(self):
        return self._wrap_method()

    @add_serverclass_doc(SenAUXServer)
    def disable_pd1(self):
        return self._wrap_method()

    @add_serverclass_doc(SenAUXServer)
    def enable_pd2(self):
        return self._wrap_method()

    @add_serverclass_doc(SenAUXServer)
    def disable_pd2(self):
        return self._wrap_method()

    @add_serverclass_doc(SenAUXServer)
    def pulse_f1(self, n: int, w: int):
        return self._wrap_method()

    @add_serverclass_doc(SenAUXServer)
    def pulse_f2(self, n: int, w: int):
        return self._wrap_method()

    # Thinly wrapped Telemetry methods
    @add_serverclass_doc(SenAUXServer)
    def status_pd1(self) -> bool:
        return self._wrap_method()

    @add_serverclass_doc(SenAUXServer)
    def status_pd2(self) -> bool:
        return self._wrap_method()

    @add_serverclass_doc(SenAUXServer)
    def adc_readmv(self, channel: int) -> float:
        return self._wrap_method(channel)

    @add_serverclass_doc(SenAUXServer)
    def adc_biasresistor(self, channel: int) -> Tuple[float, float]:
        return self._wrap_method(channel)

    # Wrapped telemetry methods
    def adc_readresistor(self, channel: int):
        """
        Reading the resistor values connected to the readout channel based on
        the bias resistor configurations. Units in Ohm.
        """
        assert 1 <= channel <= 3
        vdd = self.senaux_adc_readmv(0)
        vt = self.senaux_adc_readmv(channel)
        r1, r2 = self.senaux_adc_biasresistor(channel)
        # Voltage divider configuration:
        # vt = vdd * (R + R2) / (R + R1+R2)
        return (vt * (r1 + r2) - vdd * r2) / (vdd - vt)

    # TODO: Handling the conversion of resistor values as thermistor temperature readout


if __name__ == "__main__":
    import argparse
    import logging
    import time

    from zmq_client import HWControlClient

    parser = argparse.ArgumentParser(
        "SenAUX_methods.py",
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
    # client.reset_gcoder_device(args.devpath)
    client.senaux_enable_pd1()
    time.sleep(1)
    client.senaux_disable_pd1()

    print("VDD voltage:", client.senaux_adc_readmv(0))
    print("C1 voltage [mV]", client.senaux_adc_readmv(1))
    print("C1 bias resistors [Ohm]", client.senaux_adc_biasresistor(1))
    print("C1 resistance [Ohm]", client.senaux_adc_readresistor(1))

    client.close()
