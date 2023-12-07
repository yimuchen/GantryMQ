# Various method defined on the server-side methods
def register_method_for_client(cls):
    for method in [
        # Operation methods
        "reset_rigolps_device",
        "set_rigol_sipm",
        "set_rigol_led",
        # Telemetry methods,
        "get_rigol_sipm",
        "get_rigol_led",
    ]:
        cls.register_client_method(method)
