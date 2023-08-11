# Gantry MQ

Controlling the gantry and accompanying hardware attached to a Raspberry Pi
through a message queue system. This allows gantry related hardware to be
elegantly detached and reattached while the hardware is physically moved to
different quality assurance test stations.

The server and client side will be kept in the same library to ensure feature
parity between functionalities available at the server and what is exposed for
the client can be maintained within the same code base. The installation
instructions for the server and the client, however is fundamentally different.

## Setting up the server

### Prerequisites

Here we are assuming that the server will be ran on a Raspberry Pi. Modify the
`/boot/config.txt` file so that PWM and I2C interfaces are available: add the
following lines to the _after_ the kernel loading line:

```bash
dtoverlay=pwm-2chan
dtparam=i2c_arm=on
```

Next, we create new permission groups to avoid running the master program as
root. If you are testing this program on your personal machine, do **not** add
yourself to the `gpio` and `i2c` groups, as these devices are typically reserved
for temperature monitor and control system on typical computer laptop. Randomly
changing `i2c` and `gpio` value **will** damage your device.

```bash
groupadd -f -r pico
usermod -a -G pico ${USER}
groupadd -f -r drs
usermod -a -G drs ${USER}
## DO NOT ADD!! unless you are sure of what you are doing!
# groupadd -f -r gpio
# usermod -a -G gpio ${USER}
# groupadd -f -r i2c
# usermod -a -G i2c ${USER}
```

Then, copy the custom `udev` rules to expose device IDs to the various groups.

```bash
cp external/rules/pico.rules  /etc/udev/rules/
cp external/rules/drs.rules   /etc/udev/rules/
## DO NOT ADD unless you are sure of what you are doing!!
# cp external/rules/digi.rules  /etc/udev/rules/
```

Reboot the Raspberry Pi board to have everything take effect. If you are running
servers for testing, the software can still be installed and run without the
permission setup above, but hardware control will not function properly
(hardware initialization would likely throw an error). You will, however, still
need to install the following software requirements:

- `git`, `wget` for getting the code base
- `g++` and `cmake3`: for compiling the code. The compiler should support C++17
- `pybind11` and python headers: for exposing C++ code to python
- `fmt`: a standardized C++ formatting library
- `wxWidget`, `libusb`: for interfacing with the DRS4 headless oscilloscope.
- `python-pika`: for the rabbit-MQ system used for client-server communication.

### Installing the Server software

This can be done with direct command copy and paste:

```bash
git clone https://github.com/UMDCMS/GantryMQ.git
cd GantryMQ
./external/fetch_external.sh # Getting external libraries
cmake ./
cmake --build ./
```

This would set up all the environment for running the server.

### Testing hardware interactions locally on the server

TBD

### Starting the server software

TBD

## Setting up client software

The client software is written in pure python, and can be installed using pip to
the python virtual environment:

```bash
python -m pip install https://github.com/UMDCMS/GantryMQ.git
```

This will give you the `gmqclient` module in your python environment with the
various control clients to be used.
