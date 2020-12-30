import socket


class DateCompareException(Exception):
    pass

class InvalidSettingsException(Exception):
    pass

class ThermometerDirectException(socket.timeout):
    pass

class ThermometerLocalTimeout(socket.timeout):
    pass

class UnknownException(socket.timeout):
    pass
