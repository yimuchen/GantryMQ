# Gantry MQ server-side configurations

Instruction for setting up the message queue server systems. USB devices
(camera, 3d printer, the DRS oscilloscope, the RIGOL power supply) are
effectively plug-and-play, all you need to make sure is the device paths match
that is used for the various hardware interfaces of interest.

The bulk of the instructions here concern the use of the auxiliary control and
monitor boards designed in [this repository][sipmcalibhw]. These are the main
checklists that will be required for the various methods. Also double-check the
main [wiring diagram][wiring] for the recommended wiring configurations.

## The configuration JSON file should be given in the following format:

```json
{
    "port": 8989,
    "camera_device": "/dev/video0",
    "gcoder_device": "/dev/ttyUSB0",
    "drs_enable": true,
    "rigol_enable": true
}
```

The port dictates which network port the server should listen for client-side
instructions. The camera/gcoder/drs/rigol parameter are used to list which
hardware interfaces should be instantiated on server start-up. You may omit
these entries if you wish to use the system without certain devices. Additional
entries are required for using the auxiliary board, which will be listed below.

______________________________________________________________________

## Using the HV/LV control board

### Prerequisites

The following instructions concern the use of [this board][hvlvboard]. Before
using the board, you will need to check:

- The GPIO pin used for HV switching. This can **not** be checked in software,
  and can only be checked by looking at the jumper configuration. Also notice
  that the GPIO pin numbers correspond to GPIO logic numbers, not the physical
  pin number on the 40-pin connector. Consult the official documentation to see
  the mapping:
  https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio
- I2C address pin of the ADC. The pin configuration used would indicate the
  last bit of the address, and you can add the bit value to the `0b1001000`
  (`0x48`) prefix of the [`ads1115`][ads1115].
- The I2C address pin of the DACs. The pin configuration used would indicate
  the last bit of the address, then add this bit number to the `0b110100X`
  (`0x6X`) prefix used by the [`MCP4725`][mcp4725]. You may need to consult the
  person who assembled the board to know which skew was used.

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

Having obtained the hardware configuration, you will need to place the
following entries in the server configuration JSON files:

```json
{
  "HV_ENABLE_GPIO": "27",
  "HVLV_ADC_ADDR": "0x48",
  "HV_DAC_ADDR": "0x65",
  "LV_DAC_ADDR": "0x64"
}
```

______________________________________________________________________

## Using the Sensor auxiliary control board

### Prerequisites

The following instructions concern the use of [this board][sensauxboard]. Before
using the board, you will need to check:

- The GPIO pins used for power delivery switching.
- The GPIO pins used to trigger signal delivery. Notice that GPIO pins can
  **not** be checked in software, and can only be checked by looking at the
  jumper configuration.
- I2C address pin of the ADC. The pin configuration used would indicate the
  last bit of the address, and you can add the bit value to the `0b1001000`
  (`0x48`) prefix of the [`ads1115`][ads1115].
- The voltage dividing scheme used by the ADC measurements. Check the hardware
  instructions of the auxiliary sensor board.

After confirming the hardware configuration, you will need to include the
following entries in the server configuration JSON file.

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

The values `"C[X]"` used for the ADC will be used to indicate how the
additional voltage divider around the channel inputs are configured, with the
first value being the resistor value between the power rail and the SMA central
terminal, and the second value being the resistor value between the SMA shield
and the board ground.

## Running the server directly

After preparing the configuration JSON file, you can start the server using the
following command:

```bash
cd src/gmqserver
python run_server.py "your_config.json"
```

This will start a server with all possible hardware control interfaces listed.
Notice that this server will have commands to reset instantiate all defined
hardware interfaces, even those that are not explicitly defined in the
configuration file. If you want to spin up a server that only contain commands
to control a certain subsystem (usually for testing). Then you can run the
command:

```bash
cd src/gmqserver
python <hardware_method>.py "your_config.json"
```

Notice that this should only be used for testing purposes.

TIP: Snippets of configurations can be found the `config/server` directory,
separated by various hardware interfaces. You can use these as a template to
formulate a complete configuration using the provided `jq` tool:

```bash
jq -s 'add' config/server/port.json config/server/camera.json > config.json
```

## Running the server as a `systemd` service

To keep the server running even after you have disconnected the SSH session,
the recommended method is to run the server as a `systemd` service. Services
should only be used when the full system is fixed. Therefore, you should only
use this method when you have a working full configuration.

Generate the service file using the following commands:

```bash
cd src/gmqserver
python create_systemd_service.py "your_config.json"
```

This will place a copy of the appropriate files, in the desired location. You
can then start/stop the service using the command:

```bash
systemctl --user start/stop gantrymq.service
```

Once the service is started, you can safely disconnect, and the service will be
kept running until explicitly told to stop or if the Raspberry Pi is shutdown.
Also note that once service files are created, you can start/stop the service
immediate after logging in, no additional configuration will be needed.
To quickly check the status of the service, you can run the command:

```bash
systemctl --user status gantrymq.service
```

For a more detailed log, including all passed message in case some device is
causing issues, you can run the command:

```bash
journalctl --user-unit gantrymq
```

[ads1115]: https://www.ti.com/lit/ds/symlink/ads1115.pdf
[hvlvboard]: https://github.com/UMDCMS/SiPMCalibHW/tree/main/_manual#the-highlow-voltage-control-and-monitoring-hat-style-board
[mcp4725]: https://ww1.microchip.com/downloads/aemDocuments/documents/MSLD/ProductDocuments/DataSheets/MCP4725-Data-Sheet-20002039E.pdf
[sensauxboard]: https://github.com/UMDCMS/SiPMCalibHW/tree/main/_manual#auxillary-monitor-and-power-driving-hat-board
[sipmcalibhw]: https://github.com/UMDCMS/SiPMCalibHW/tree/main/_manual
[wiring]: https://github.com/UMDCMS/SiPMCalibHW/blob/pdfs/schematics/wiring.pdf
