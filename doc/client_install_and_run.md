# Running and installing the client

As the client aims to be pure python, it is recommended to install the client
using the python environment. The recommended method would be using
[`conda`][conda].

## Installing the new package

As this gantry version is expected to be used as a separate package. Notice
that the installation of the environment is expected to one of potentially many
dependencies, the working directory is intentionally 1-level higher than the
git-managed directory. The example `environment_client.yaml` is only used as an
example, eventually you should use define your own.

```bash
mkdir workdir
cd workdir
git clone https://github.com/UMDCMS/GantryMQ
conda env create --file GantryMQ/environment_client.yaml
```

With this you should be able to activate the environment like:

```bash
conda activate gantrymq_client
```

The following instructions will assume that you are working in this `conda`
environment.

## Executing client-side code

You can interact with the hardware interactively directly in a python shell, or
by running a script. Since this uses the same syntax, the following instruction
will simply use a plain python script, and we assume that you know the IP and
network port of the server-side configuration.

Interacting with the hardware managed by the server can be done simply as:

```python
import gmqclient

client = gmqclient.create_default_client(_IP_, _PORT_)

# Example of setting the low voltage bias on the HV/LV power board
client.set_lv_bias(554)  # Units in mV
print(client.get_lv_mv())

# Example of controlling the gantry system
client.move_to(10, 20, 30)  # Units in mm
client.send_home()  # Moving back to (0,0,0)
print(client.get_coord())  # Returning the (x,y,z) coordinates in mm

# Example of settings the getting the camera image buffer (as a numpy array)
img = client.get_frame()
print(img)

# Example of getting and settings the various in the DRS4
client.drs_set_rate(2.0)  # Set to 2.0 GHz
```

You can check all the methods that can be used by looking at the methods listed
in the various modules in the `src/gmqserver/*_method.py` files. Notice you can
also reset the hardware handled on the server side, typically with a method
call like:

```python
client.reset_camera_device("/dev/video1")
```

But because that you know what you are doing before running such commands.

When either the code completes, or you when you exit the interactive python
shell, the connection will be cleanly disconnected, and the hardware will be
left as is on the server side.

## Types of commands

The methods that can be called can broadly be separated into

- Operation commands: command that modify the hardware states, and therefore
  should only be uniquely controlled by a single user.

- Telemetry commands: command that does not intrinsically modify the hardware
  state, and could be called by multiple users that might be interested in
  monitoring the hardware state.

For operation commands, the first client that connects and requests one
operation command will claim effective ownership of all hardware on the
server-side, and will retain ownership until disconnected or the
`client.release_operator()` method is called. In the case the server is stuck
thinking a non-existence server exists (typically when a client-side code
exited ungracefully), one can force claim the ownership with the method
`client.claim_operator()`, though beware that this mean that other clients may
misbehave.

## Extended data processing

The design of the software is to have the server-side perform as little data
processing as possible. All complicated data processing should be handled
client side to keep everything as flexible as possible. There are certain
single-hardware data processing methods that is also provided in the
client-side code base, though by-design, they may be superseded by whatever
data processing is needed:

- `camera_methods`: additional methods for finding the SiPM (a dark rectangle)
  in the camera view port.

- `senaux_method`: Adds additional `client.senaux_adc_read*` to interpret
  results from raw voltage readouts to either resistor values (units in Ohm),
  corresponding NTD thermistor temperatures (units in C) or Platinum PTD
  temperatures (units in C).

[conda]: https://conda.io/projects/conda/en/latest/index.html
