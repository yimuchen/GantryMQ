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
        """Adding hard count limit to avoid client/serve desync"""
        assert n <= 10_000, "Do not set pulse count larger than 10K"
        return self._wrap_method(n, w)

    @add_serverclass_doc(SenAUXServer)
    def pulse_f2(self, n: int, w: int):
        """Adding hard count limit to avoid client/serve desync"""
        assert n <= 10_000, "Do not set pulse count larger than 10K"
        return self._wrap_method(n, w)

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
        vdd = self.adc_readmv(0)
        vt = self.adc_readmv(channel)
        r1, r2 = self.adc_biasresistor(channel)
        # Voltage divider configuration:
        # vt = vdd * (R + R2) / (R + R1+R2)
        return (vt * (r1 + r2) - vdd * r2) / (vdd - vt)

    # TODO: Handling the conversion of resistor values as thermistor temperature readout
