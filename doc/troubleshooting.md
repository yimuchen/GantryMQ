# Troubleshooting

Some common issues that can occur when using the system.

## Failing to set up GPIO devices

This can be identified with the error message:

```
RuntimeError: Error writing [0x3237] to file descriptor [/sys/class/gpio/export].
```

Or similar when attempting to reset a GPIO device. This typically occurs is a
previous instance of the server was not terminate gracefully. In such cases,
you can reset the GPIO pins by running the following command on the RPi:

```bash
echo "27" > /sys/class/gpio/unexport
```

Change "27" to which ever GPIO is the offending pin

