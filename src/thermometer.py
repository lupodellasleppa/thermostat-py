#!/usr/bin/python3

import asyncio
import json
import logging
import os
import socket

from exceptions import *


class ConfigurationError(BaseException):
    pass


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
            logging.info("Requesting temperatures...")
        except socket.timeout:
            raise ThermometerLocalTimeout
        temperature = await self._parse_temperatures(
            request.decode(), 'celsius'
        )
        return temperature


class ThermometerDirect():
    """
    For future implementation of temperature sensor
    directly attached to RaspberryPi
    """
    def __init__(self):
        if not self.check_pin_configuration():
            raise ConfigurationError(
                "GPIO pins are not correctly configured"
                " to read from temperature sensor."
            )

    def check_pin_configuration(self):
        with open('/boot/config.txt') as f:
            config = f.readlines()
        # check there's a line beginning with dtoverlay=w1-gpio
        if any([x.strip().startswith('dtoverlay=w1-gpio') for x in config]):
            return True

    async def request_temperatures(self):
        devices_dir = '/sys/bus/w1/devices'
        devices = os.listdir(devices_dir)
        for device in devices:
            if device.startswith('28'):
                thermometer = os.path.join(devices_dir, device)
        data = os.path.join(thermometer, 'w1_slave')
        with open(data) as f:
            try:
                temperature = int(
                    f.readlines()[-1]
                    .split('=')[-1]
                ) / 1000
            except IndexError as e:
                raise ThermometerDirectException(e)
        return temperature
