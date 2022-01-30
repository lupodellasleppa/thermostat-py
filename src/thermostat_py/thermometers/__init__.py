from .validators import (
    ThermometerModel,
    ThermometerWiredModel,
    ThermometerWirelessModel
)


class Thermometer():
    def __init__(
        self,
        name,
        description,
        read_period,
        thermometer_type,
        target_temperature
    ):
        self.name = name
        self.description = description
        self.type = type


class ThemometerWireless(Thermometer):
    def __init__(self, host, port, send_period, timeout):
        super().__init__()
        self.host = host
        self.port = port
        self.send_period = send_period
        self.timeout = timeout


class ThermometerWired(Thermometer):
    def __init__(self, host, port):
        pass


class ThermometerManager():
    def __init__(self):
        self.thermometers = {}
