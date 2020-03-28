#!/usr/bin/python3

import asyncio
import json
import logging
import socket


class Thermometer():

    def __init__(self, ip, port, timeout):

        self.ip = ip
        self.port = port

        self.thermometer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.thermometer.settimeout(timeout)
        self.thermometer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    async def _parse_temperatures(self, data, measure):

        temperature = json.loads(data.decode())

        return temperature[measure]

    async def request_temperatures(self):

        self.thermometer.sendto(b'temps_req', (self.ip, self.port))

        temperature = await self._parse_temperatures(
            self.thermometer.recv(4096), 'celsius'
        )

        return temperature
