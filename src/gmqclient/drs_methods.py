import numpy

from .server import drs_methods
from .zmq_client import HWClientInstance, add_serverclass_doc


class DRSDevice(HWClientInstance):
    def __init__(self, name):
        super().__init__(name)

    # Most operation methods are simple pass-through methods
    @add_serverclass_doc(drs_methods.DRSDevice)
    def set_trigger(self, channel: int, level: float, direction: int, delay: float):
        return self._wrap_method(channel, level, direction, delay)

    @add_serverclass_doc(drs_methods.DRSDevice)
    def set_samples(self, n: int):
        return self._wrap_method(n)

    @add_serverclass_doc(drs_methods.DRSDevice)
    def set_rate(self, rate: float):
        return self._wrap_method(rate)

    @add_serverclass_doc(drs_methods.DRSDevice)
    def start_collection(self):
        return self._wrap_method()

    @add_serverclass_doc(drs_methods.DRSDevice)
    def force_stop(self):
        return self._wrap_method()

    def _run_calibration(self):
        """
        Running the underlying calibration, which assumes all hardware has been
        correctly configured for calibration. Explicitly hiding this raw
        functionality, as some message should be passed to the user.
        """
        return self.client.run_function(self.name, "run_calibration")

    # All telemetry methods are simple passthrough methods
    @add_serverclass_doc(drs_methods.DRSDevice)
    def get_time_slice(self) -> numpy.ndarray:
        return self._wrap_method()

    @add_serverclass_doc(drs_methods.DRSDevice)
    def get_waveform(self) -> numpy.ndarray:
        return self._wrap_method()

    @add_serverclass_doc(drs_methods.DRSDevice)
    def get_trigger_channel(self) -> int:
        return self._wrap_method()

    @add_serverclass_doc(drs_methods.DRSDevice)
    def get_trigger_direction(self) -> int:
        return self._wrap_method()

    @add_serverclass_doc(drs_methods.DRSDevice)
    def get_trigger_level(self) -> float:
        return self._wrap_method()

    @add_serverclass_doc(drs_methods.DRSDevice)
    def get_trigger_delay(self) -> float:
        return self._wrap_method()

    @add_serverclass_doc(drs_methods.DRSDevice)
    def get_samples(self) -> int:
        return self._wrap_method()

    @add_serverclass_doc(drs_methods.DRSDevice)
    def is_ready(self) -> bool:
        return self.is_ready()
