# Gantry MQ instruction manual

Instruction for setting up the message queue server systems. USB devices
(camera, 3d printer, and the DRS oscilloscope) are effectively plug-and-play,
all you need to make sure is the device paths match that is used for the various
hardware interfaces of interest.

The bulk of the instructions here concern the use of the auxiliary control and
monitor boards designed in [this repository][SiPMCalibHW]. These are the main
checklists that will be required for the various methods.

---

## Using the HV/LV control board

### Prerequisites

The following instructions concern the use of [this board][HVLVboard]. Before
using the board, you will need to check:

- The GPIO pin used for HV switching. This can _not_ be checked in software,
  and can only be checked by looking at the jumper configuration.
- I2C address pin of the ADC. The pin configuration used would indicate the last
  bit of the address, and you can add the bit value to the `0b1001000` (`0x48`)
  prefix of the [`ads1115`][ads1115].
- The I2C address pin of the DACs. The pin configuration used would indicate the
  last bit of the address, then add this bit number to the `0b110100X` (`0x6X`)
  prefix used by the [`MCP4725`][MCP4725]. You may need to consult the person who assembled the board to know which skew was used.

For the I2C address, you can also use the built-in Linux tool `i2cdetect` to
find which I2C addresses have an active device.

```bash
> i2cdetect  -y 1
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:                         -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
40: -- -- -- -- -- -- -- -- 48 -- -- -- -- -- -- --
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
60: -- -- -- -- 64 65 -- -- -- -- -- -- -- -- -- --
70: -- -- -- -- -- -- -- --
```

The output example above shows that addresses `0x48`, `0x64` and `0x65` have
devices that can be used, though you still need to determine which device
corresponds to which address using the physical configuration of the board.

Having obtained the hardware configuration, you will need to prepare the
following JSON file on the server side

```json
{
  "HV_ENABLE_GPIO": "27",
  "HVLV_ADC_ADDR": "0x48",
  "HV_DAC_ADDR": "0x65",
  "LV_DAC_ADDR": "0x64"
}
```

All entries should use strings to indicate the addresses of the required target.

### Setting up the server-side code

Assuming you have set up the server-side environment as described in the
documentation, you can then run:

```bash
cd GantryMQ/src/gmqserver
python HVLV_methods.py "your_config.json"
```

This will create a server on port 8989. And will continue to run until you hit
`CTRL+C` on the server side. A default JSON file has been provided as
`config/server/HVLV_example.json` in this repository.

### Setting up the client-side code

On the client side, again assuming you have set up the software environment as
indicated in the stack: you should be able to run the Python script:

```bash
python src/gmqclient/HVLV_methods.py
```

Alternatively, you can run the client interactively if you have to manually
perform adjustments on the fly:

```bash
python # Start the python shell in the client side software
### The following section is required
>>> import gmqclient
>>> gmqclient.HVLV_methods.register_method_for_client(gmqclient.HWControlClient)
>>> client = gmqclient.HWControlClient(_IP_, _PORT_) # You will need to obtain server configuration
>>> client.claim_operator()

### The following can them be whatever instruction you are interested in.
>>> client.hv_enable() #
>>> client.set_lv_bias(0.554) # Units in MV.
>>> client.get_lv_mv() #
0.5534 ## Printing units in MV
```

For the full list of allowed instructions, see the strings listed in
`src/gmqclient/HVLV_methods.py`.

[SiPMCalibHW]: https://github.com/UMDCMS/SiPMCalibHW/tree/main/_manual
[HVLVboard]: https://github.com/UMDCMS/SiPMCalibHW/tree/main/_manual#the-highlow-voltage-control-and-monitoring-hat-style-board
[ads1115]: https://www.ti.com/lit/ds/symlink/ads1115.pdf
[MCP4725]: https://ww1.microchip.com/downloads/aemDocuments/documents/MSLD/ProductDocuments/DataSheets/MCP4725-Data-Sheet-20002039E.pdf

---

## Using the Sensor auxillary control board

### Prerequisites

The following instructions concern the use of [this board][SensAUXboard]. Before
using the board, you will need to check:

- The GPIO pins used for power delivery switching.
- The GPIO pins used to trigger signal delivery. Notice that GPIO pins can _not_
  be checked in software, and can only be checked by looking at the jumper
  configuration.
- I2C address pin of the ADC. The pin configuration used would indicate the last
  bit of the address, and you can add the bit value to the `0b1001000` (`0x48`)
  prefix of the [`ads1115`][ads1115].

After confirming the hardware configuration, you will need to prepare a JSON
file in the following format:

```json
{
  "SENAUX_PD1_GPIO": "22",
  "SENAUX_PD2_GPIO": "23",
  "SENAUX_F1_GPIO": "20",
  "SENAUX_F2_GPIO": "21",
  "SENAUX_ADC": {
    "ADDR": "0x49",
    "C1": [10000, 0],
    "C2": [10000, 0],
    "C2": [10000, 0]
  }
}
```

The values `"C[X]"` used for the ADC will be used to indicate how the additional
voltage divider around the channel inputs are configured.

### Setting up the server-side software

Assuming you have set up the server-side environment as described in the
documentation, you can then run:

```bash
cd GantryMQ/src/gmqserver
python SenAUX_methods.py "your_config.json"
```

This will create a server on port 8989. And will continue to run until you hit
`CTRL+C` on the server side. A default JSON file has been provided as
`config/server/SenAUX_example.json` in this repository.

### Setting up the client-side software

On the client side, again assuming you have set up the software environment as
indicated in the stack: you should be able to run the Python script:

```bash
python src/gmqclient/SenAUX_methods.py
```

Alternatively, you can run the client interactively if you have to manually
perform adjustments on the fly:

```bash
python # Start the python shell in the client side software
### The following section is required
>>> import gmqclient
>>> gmqclient.HVLV_methods.register_method_for_client(gmqclient.HWControlClient)
>>> client = gmqclient.HWControlClient(_IP_, _PORT_) # You will need to obtain server configuration
>>> client.claim_operator()

### The following can them be whatever instruction you are interested in.
>>> client.hv_enable() #
>>> client.set_lv_bias(0.554) # Units in MV.
>>> client.get_lv_mv() #
0.5534 ## Printing units in MV
```

TBD

[SensAUXBoard]: https://github.com/UMDCMS/SiPMCalibHW/tree/main/_manual#auxillary-monitor-and-power-driving-hat-board
