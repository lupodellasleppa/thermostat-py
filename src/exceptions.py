import socket


class DateCompareException(Exception):
    pass


class InvalidSettingsException(Exception):
    pass


class ThermometerDirectException(Exception):
    pass


class ThermometerLocalException(Exception):
    pass


class ThermometerLocalTimeout(socket.timeout):
    pass


class UnknownException(socket.timeout):
    pass
