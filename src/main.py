#!/usr/bin/python3

import asyncio

from program import Program
from relay import Relay
import settings_handler
from thermometer import Thermometer
import util


def main():

    # load settings
    settings = settings_handler.load_settings(settings_path)
    # instantiate thermometer
    thermometer_ip, thermometer_port = settings['configs']
    thermometer = Thermometer(thermometer_ip, thermometer_port, 60)
    # instantiate relay
    relay = Relay()
