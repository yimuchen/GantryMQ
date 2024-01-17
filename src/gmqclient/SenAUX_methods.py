## Direct methods to be overloaded onto the client
from typing import Tuple, Dict, List


# Basic methods for accessing the various methods
def register_method_for_client(cls):
    for method in [
        # Operation methods
        "reset_senaux_devices",
        "senaux_enable_pd1",
        "senaux_disable_pd1",
        "senaux_enable_pd2",
        "senaux_disable_pd2",
        "senaux_pulse_f1",
        "senaux_pulse_f2",
        # Telemetry methods,
        "senaux_status_pd1",
        "senaux_status_pd2",
        "senaux_adc_readmv",
        "senaux_adc_biasresistor",
    ]:
        cls.register_client_method(method)

    # Reading voltage as resistance value
    def senaux_adc_readresistor(self, channel: int):
        assert 1 <= channel <= 3
        vdd = self.senaux_adc_readmv(0)
        vt = self.senaux_adc_readmv(channel)
        r1, r2 = self.senaux_adc_biasresistor(channel)
        # Voltage divider configuration:
        # vt = vdd * (R + R2) / (R + R1+R2)
        return (vt * (r1 + r2) - vdd * r2) / (vdd - vt)

    # TODO: implement standard thermistor and PTD temperature conversion

    setattr(cls, "senaux_adc_readresistor", senaux_adc_readresistor)


if __name__ == "__main__":
    from zmq_client import HWControlClient
    import argparse
    import time
    import logging

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
