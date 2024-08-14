# Installation instruction of a Raspberry Pi for deployment

Contact the system administrator if you want a directly deployable image file
that you can flash to your SD card. This file contains the instruction for
building the image from scratch using the standard tools.

## Preparing the base image

The base image for the Raspberry Pi OS can be found [here][rpios], just follow
the main instructions here. Notice that this instruction assumes that you are
using a Raspberry Pi 4.

### First page:

- Device type: RASPBERRY PI 4
- Operating system: Raspberry Pi OS (64bit)
- Storage: "your SD card device path"

### Second page

- Configuration:
  - Enable ssh, and set default username

At this point should be prompted to write the image to your SD card. This will
take around 20 minutes to complete.

## Setting up internet connect

This is sensitive information and will need to be handled by a case-by-case
basis. Contact you institute IT to find what works best for the network settings
for you institute. The Raspberry Pi OS contains a GUI by default, so you can
connect up the Raspberry Pi to a monitor and pull the required information
before one can get the networking setup.

## Setting up device permissions

Once log onto the device, run the command `sudo raspi-config` and in the
"Interfaces options" section, enable the SSH, I2C interfaces. This
automatically sets up the permission on the RPi allow for I2C interface handling.

Additionally, to use the DRS device as a non-root users, you will need to set
yourself up to a custom group. The permissions for setting up the system to 
recognize the devices will be described latter.

```bash
groupadd -f -r drs
usermod -a -G drs ${USER}
```

Reboot the Raspberry Pi board to have everything take effect.

## Installing common C++/Python dependencies

All C++ related dependencies are available in the Raspberry Pi/Ubuntu
repository. Run the following `apt` commands to make sure all commands are
available.

```bash
# Update repository information
sudo apt update
# For compiling the C/C++ libraries and python bindings
sudo aptinstall git cmake python3-pybind11 pybind11-dev libfmt-dev libgpiod-dev
# For compiling the DRS software
sudo apt install libwxgtk3.2-dev libusb-dev libusb-1.0-0-dev
# For python requirements
sudo apt install python3-zmq python3-opencv python3-scipy python3-pyvisa
# Additional tools that can help with operations and configuration
sudo apt install jq
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

Also, copy the custom `udev` rules to expose device IDs to the various groups.

```bash
cp external/rules/drs.rules   /etc/udev/rules.d/
```

You will need to reboot for the all changes to take effect.

Notice that this only includes the dependencies. As configurations will require
knowledge of how the various hardware is connected. For the continued
documentation of how to properly configure the software according to the
hardware configuration, see the file ["server-side
configuration"](./config_server.md).

[rpios]: https://www.raspberrypi.com/software/
