# Gantry MQ

Controlling the gantry and accompanying hardware attached to a Raspberry Pi
through a message queue system. This allows gantry-related hardware to be
elegantly detached and reattached while the hardware is physically moved to
different quality assurance test stations.

The server and client side will be kept in the same library to ensure feature
parity between functionalities available at the server and what is exposed for
the client can be maintained within the same code base. The installation
instructions for the server and the client, however, are fundamentally different.

## Setting up the server

For the full instructions, see the instructions [here](doc/install_server.md)
to install the prerequisites and [here](doc/config_server.md) to perform
additional software configuration to run the server. The bulk of the
requirements should have been repaired by the system administrators already.

## Setting up the client-side software

The full instruction should be listed [here](./doc/client_install_and_run.md).

## Testing hardware interactions

If you wish to install the server-side code on your personal machine to test
potential server-client interaction, you can find how to do so
[here](./doc/install_local_testing.md), the client-side installation is
identical for installing on your personal machine.

## Testing just the hardware interactions

Once the server-side software is installed, we can test the hardware
interaction on the server machine to make sure everything is working nominally
on the server side. The following commands will likely not work in the testing
machine, as they assume that you have access to the various hardware
interfaces. You may also need to modify the access addresses and pins to match
whatever hardware is attached to your system.

```python
cd GantryMQ # Tests are not intended to be ran anywhere else other than the project directory
PYTHONPATH=$PYTHONPATH:$PWD python tests/hardware/gcoder.py # Testing gcoder
PYTHONPATH=$PYTHONPATH:$PWD python tests/hardware/gpio.py   # Testing GPIO interactions
PYTHONPATH=$PYTHONPATH:$PWD python tests/hardware/i2c_ads1115.py # Testing the I2C ADC interaction
PYTHONPATH=$PYTHONPATH:$PWD python tests/hardware/i2c_mcp4725.py # Testing the I2C DAC interaction
```
