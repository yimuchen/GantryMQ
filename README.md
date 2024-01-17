# Gantry MQ

Controlling the gantry and accompanying hardware attached to a Raspberry Pi
through a message queue system. This allows gantry-related hardware to be
elegantly detached and reattached while the hardware is physically moved to
different quality assurance test stations.

The server and client side will be kept in the same library to ensure feature
parity between functionalities available at the server and what is exposed for
the client can be maintained within the same code base. The installation
instructions for the server and the client, however, are fundamentally different.

The instruction here will be concerned with software deployment. To see the
instructions for local testing, see [`doc/local.md`](doc/local.md). As the
software prerequisite on the server side is also rather long, see the
[`doc/install_server.md`](doc/install_server.md) for detailed instructions
there.

## Setting up the server

For the full instructions, see the instructions [here](doc/install_server.md),
but the bulk of the requirements should have been repaired by the system
administrators already.

Here we just remind you that the Python environment needs to be set up
appropriately for a newly logged-in session, if the required environment has not
been set up globally:

```bash
cd GantryMQ
export PYTHONPATH=$PYTHONPATH:$PATH
```

## Setting up the client-side software

As the client-side software does not require additional permissions or hardware,
the safest way would be to download the repository and install the package as a
pip package:

```bash
git clone https://github.com/UMDCMS/GantryMQ.git
python -m venv gantryenv
source gantryenv/bin/activate
python -m pip install ./GantryMQ
```

Notice that you will need to reload the Python virtual environment every time.

## Testing hardware interactions

### Locally on the server machine

Once the server-side software is installed, we can test the hardware interaction
on the server machine to make sure everything is working nominally on the server
side. The following commands will likely not work in the docker session. The
commands here also assume that you have access to the various hardware
interfaces. You may also need to modify the access addresses and pins to match
whatever hardware is attached to your system.

```python
cd GantryMQ # Tests are not intended to be ran anywhere else other than the project directory
PYTHONPATH=$PYTHONPATH:$PWD python tests/hardware/gcoder.py # Testing gcoder
PYTHONPATH=$PYTHONPATH:$PWD python tests/hardware/gpio.py   # Testing GPIO interactions
PYTHONPATH=$PYTHONPATH:$PWD python tests/hardware/i2c_ads1115.py # Testing the I2C ADC interaction
PYTHONPATH=$PYTHONPATH:$PWD python tests/hardware/i2c_mcp4725.py # Testing the I2C DAC interaction
```

### Testing with server-client interactions

The various modules defined in the `src/gmqserver` and `src/gmqclient`
directories provide example scripts for testing single hardware interactions.
The following instruction assumes that you are in the `GantryMQ` for both the
server and the client-side machine. Notice additional methods command line
arguments can be passed to the client-side script to modify the behavior, as by
default, the client will attempt to connect to the server running on the local
machine. Once the server is spawned, hit Ctrl+C to exit the server.

#### Testing the ZMQ server functionality

```bash
# Server-side
python src/gmqserver/zmq_server.py
# Client-side
python src/gmqclient/zmq_client.py
```

#### Testing the various control systems

Currently implemented systems include `gcoder`, `camera`, `drs`, `rigol`, `HVLV`
and `SenAUX`. Make sure that the connected hardware is visible to the server
before attempting to run the following instructions.

```bash
# Server-side
python src/gmqserver/${system}_methods.py --help
# Client-side
python src/gmqclient/${system}_methods.py --help
```

For other interactions, because interactions with the ICs on the auxiliary
helper boards need to be set up according to the required specs, consult the
documentation found in the [`doc/aux_board.md`](doc/aux_board.md) or similar for
detailed instructions.

## Preparing the deployment server

To deploy a server, you can run the following command on the server machine:

```bash
cd GantryMQ/src/gmqserver
python3 deploy.py --hw1 --hw2
```

The various deployment flags will be used to indicate how the various hardware
interfaces is set up. Run `python3 deploy.py --help` if you are unsure about
some requirements of the hardware interface.
