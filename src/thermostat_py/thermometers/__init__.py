from .validators import ThermometerWiredModel, ThermometerWirelessModel


class Thermometer():
    @classmethod
    def validate(cls, value):

        return cls.validator(**value)

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

    def __repr__(self):
        return str(self.__dict__)


class ThermometerWired(Thermometer):
    validator = ThermometerWiredModel

    def __init__(
        self,
        name,
        description,
        read_period,
        thermometer_type,
        target_temperature
    ):
        super().__init__(
            name,
            description,
            read_period,
            thermometer_type,
            target_temperature
        )


class ThermometerWireless(Thermometer):
    validator = ThermometerWirelessModel

    def __init__(
        self,
        name,
        description,
        host,
        port,
        send_period,
        timeout,
        read_period,
        thermometer_type,
        target_temperature
    ):
        super().__init__(
            name,
            description,
            read_period,
            thermometer_type,
            target_temperature
        )
        self.host = host
        self.port = port
        self.send_period = send_period
        self.timeout = timeout
