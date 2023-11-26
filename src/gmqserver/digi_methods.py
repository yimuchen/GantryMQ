from zmq_server import HWContainer

import logging


def reset_digi_devices(
    logger: logging.Logger, hw: HWContainer, devices_dict: Dict[str, Tuple[int]]
):
    """
    As there will be multiple GPIO/I2C devices of the same type, the way you
    specify the hardware creation would be to provide a dictionary with:

    - the device type as the key (can be gpio/i2c_ads1115/i2c_dac5556)
    - If the device is the GPIO type, the address should be


    """
    if not hasattr(hw, "camera_device"):
        hw.camera_device = None

    if isinstance(hw.camera_device, cv2.VideoCapture):
        hw.camera_device.release()

    # Loading the camera instance into the data set
    if "/dummy" not in dev_path:
        hw.camera_device = cv2.VideoCapture(dev_path)

        # Setting up the capture property
        hw.camera_device.set(cv2.CAP_PROP_FRAME_WIDTH, 1240)
        hw.camera_device.set(cv2.CAP_PROP_FRAME_HEIGHT, 1024)
        hw.camera_device.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Always get latest frame
        hw.camera_device.set(cv2.CAP_PROP_SHARPNESS, 0)  # Disable post processing

    # Loading a dummy camera instance
