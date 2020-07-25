import socket


class DateCompareException(Exception):
    pass

class InvalidSettingsException(Exception):
    pass

class ThermometerTimeout(socket.timeout):
    pass
