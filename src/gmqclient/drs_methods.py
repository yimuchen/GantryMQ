## Direct methods to be overloaded onto the client

# Basic methods for accessing the various methods
def register_method_for_client(cls):
    for method in [
        # Operation methods
        "force_stop",
        "start_collection",
        "run_calibration",
        "set_trigger",
        "set_samples",
        "set_rate",
        "reset_drs_device",
        # Telemetry methods
        "get_time_slice",
        "get_waveform",
        "get_trigger_channel",
        "get_trigger_direction",
        "get_trigger_level",
        "get_trigger_delay",
        "get_samples",
        "get_rate",
        "is_available",
        "is_ready",
    ]:
        cls.register_client_method("drs_" + method)
