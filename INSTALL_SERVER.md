# Installation instruction of a Raspberry Pi for deployment

Contact the system administrator if you want a directly deployable image file
that you can flash to your SD card. This file contains the instruction for
building the image from scratch using the standard tools.

## Preparing the base image

The base image for the Raspberry Pi OS can be found [here][rpiOS], just follow
the main instructions here. Notice that this instruction assumes that you are
using a Raspberry Pi 4.

### First page:

- Device type: RASPBERRY PI 4
- Operating system: Raspberry PI OS (64bit)
- Storage: "your SD card device path"

### Second page

- Configuration:
  - Enable ssh, and set default user name

At this point should be prompted to write the image to your SD card. This will
take around 20 minutes to complete.

## Setting up internet connect

This is sensitive information and will need to be handled by a case-by-case
basis. Contact you institute IT to find what works best for the network settings
for you institute. The Raspberry Pi OS contains a GUI by default, so you can
connect up the Raspberry Pi to a monitor and pull the required information
before one can get the networking setup.

## Setting up device permissions

Modify the `/boot/config.txt` file so that I2C interfaces are available. Be sure
to add the following lines to the _after_ the kernel loading line:

```bash
dtparam=i2c_arm=on
```

Next, we create new permission groups to avoid running the master program as
root. If you are testing this program on your personal machine, do **not** add
yourself to the `gpio` and `i2c` groups, as these devices are typically reserved
for temperature monitor and control system on typical computer laptop. Randomly
changing `i2c` and `gpio` value **will** damage your device.

```bash
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
cp external/rules/drs.rules   /etc/udev/rules/
## DO NOT ADD unless you are sure of what you are doing!!
# cp external/rules/digi.rules  /etc/udev/rules/
```

Reboot the Raspberry Pi board to have everything take effect.

## Installing common C++ dependencies

All C++ related dependencies are available in the Raspberry Pi/Ubuntu
repository. Run the following `apt-get` commands to make sure all commands are
available.

```bash
# Update repository information
sudo apt-get update
# For compiling the C/C++ libraries and python bindings
sudo apt-get install git cmake python3-pybind11 pybind11-dev libfmt-dev
# For compiling the DRS software
sudo apt-get install libwxgtk3.2-dev libusb-dev libusb-1.0-0-dev

# For python requirements
sudo apt-get install pyzmq opencv-python python-scipy
```

## Installing and compiling the server software

This can be done with direct command copy and paste:

```bash
git clone https://github.com/UMDCMS/GantryMQ.git
cd GantryMQ
./external/fetch_external.sh # Getting external libraries
cmake ./
cmake --build ./
```

This should install all requirements. For a simpler operation, you might want to
the following python path to the shell start up:

```bash
export PYTHONPATH=$PYTHONPATH/$HOME/GantryMQ/src/gmqserver
```

## Running the server

For running the full server, a default server is provided in the
`src/gmqserver/deploy.py` script. Which you can run directly or uses as a
template to start the required server and hardware configurations.

[rpiOS]: https://www.raspberrypi.com/software/
