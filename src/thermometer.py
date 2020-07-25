#!/usr/bin/python3

import asyncio
import json
import logging
import socket

from exceptions import *


class ThermometerLocal():
    """
    Class that handles temperature request from sensor
    attached to wifi transmitter in same network
    """

    def __init__(self, ip, port, timeout):
        self.ip = ip
        try:
            self.port = int(port)
        except ValueError as e:
            raise InvalidSettingsException(e)
        # build UDP socket
        self.thermometer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.thermometer.settimeout(timeout)
        self.thermometer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    async def _parse_temperatures(self, data, measure):
        """Async json.loads wrapper for async temperature request"""
        temperature = json.loads(data)
        return temperature[measure]

    async def request_temperatures(self):
        """Async request of temperatures"""
        self.thermometer.sendto(b'temps_req', (self.ip, self.port))
        try:
            request = self.thermometer.recv(4096)
        except socket.timeout:
            raise ThermometerTimeout
        temperature = await self._parse_temperatures(
            request.decode(), 'celsius'
        )
        return temperature

class ThermometerDirect():
    """
    For future implementation of temperature sensor
    directly attached to RaspberryPi
    """
    pass
