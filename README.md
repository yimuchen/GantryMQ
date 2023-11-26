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

The details for setting up the server software for running on the Raspberry Pi
will be detailed in the `INSTALL_SERVER.md` file, as it requires additional
hardware permission setup. Look to that file if you are attempting to set up a
new system from scratch.

For software testing, we have provided a docker file in this repository such
that users can test the software capabilities of the server before fully
deploying, to build the image file, run the following command on your machine:

```bash
docker buildx build --file tests/docker/Dockerfile --tag gantrymq   \
       --network="host"  --platform ${PLATFORM}  --rm --load ./
```

The `${PLATFORM}` variable should match what machine you are running the test
on (tested using `linux/amd64`).

To start up the docker session run the command:

```bash
docker run -it                                              \
       --network="host"                                     \
       --platform ${PLATFORM}                               \
       --mount type=bind,source="${PWD}",target=/srv        \
       --privileged -v /dev/video1:/dev/video1              \
       gantrymq:latest                                      \
       /bin/bash --init-file "/srv/tests/docker/bashrc.sh"
```

Notice that if you are running in docker, it is likely that most of the hardware
will not function, and is not strictly a bug in the system. If you want to test
the camera device, modify the exposed device.

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
side. The following commands will likely not work in the docker session

```python
cd GantryMQ # Tests are not intended to be ran anywhere else other than the project directory
PYTHONPATH=$PYTHONPATH:$PWD python tests/gcoder.py # Testing gcoder
PYTHONPATH=$PYTHONPATH:$PWD python tests/gpio.py   # Testing GPIO interactions
PYTHONPATH=$PYTHONPATH:$PWD python tests/i2c_ads1115.py # Testing the I2C ADC interaction
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

Currently implemented systems include `gcoder`, `camera`, `digi`, and `drs`. If
you are testing on your machine, various hardware interfaces may not be
available.

```bash
# Server-side
python src/gmqserver/${system}_methods.py
# Client-side
python src/gmqclient/${system}_methods.py --help
```
