#!/usr/bin/python3

import argparse
import asyncio
import datetime
import signal
import time

from program import Program
from relay import Relay
from settings_handler import SettingsHandler
from thermometer import Thermometer
import util


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('settings_path')
    args = parser.parse_args()
    return args

def _init_thermometer(settings, intervals):
    thermometer_ip, thermometer_port = settings['configs']
    return ThermometerLocal(
        thermometer_ip, thermometer_port, intervals['temperature']
    )

def _init_relay(settings, settings_path):
    return Relay(settings['relay'], settings_path)

def check_same_day(last):
    '''Returns True if day changed since last read.'''
    current = util.get_now()
    if last != current['day']:
        return True

def gwrite_temperatures(thermometer, settings_handler):
    try:
        temperature = await thermometer.request_temperatures()
        settings_handler.handler({'temperature': {'room': temperature}})
    except ThermometerTimeout:
        pass

def take_action(settings_handler, current, relay):

    settings = settings_handler.load_settings()
    mode = settings['mode']
    manual = mode['manual']
    auto = mode['auto']
    program = mode['program']
    desired_temp = mode['desired_temp']

    return _handle_on_and_off(
        current, manual, auto, program, desired_temp, room_temperature, relay
    )

def _handle_on_and_off(
        current, manual, auto, program, desired_temp, room_temperature, relay
    ):
    '''Handles all there is to turning the heater on or off.'''
    # MANUAL MODE
    if manual:
        return _manual_mode(desired_temp, room_temperature, relay)
    # AUTO MODE
    elif auto:
        return _auto_mode(desired_temp, current, relay)
    # BOTH MANUAL AND AUTO ARE OFF
    else:
        return relay.off

def _manual_mode(desired_temperature, room_temperature):
    '''
    Action to take when MANUAL mode is True.
    Manual mode prevails over auto mode and so does desired_temperature
    over numeric values in program.json
    '''
    # Room temperature is lower than desired temperature
    if room_temperature < desired_temperature:
        return relay.on
    # Room temperature satisfies desired temperature
    else:
        return relay.off

def main():

    args = create_parser()

    # load settings
    settings_handler = SettingsHandler(args.settings_path)
    settings = settings_handler.load_settings()

    log = settings['logs']
    mode = settings['mode']
    paths = settings['paths']
    intervals = settings['intervals']
    relay_configs = settings['relay']
    room_temperature = settings['temperatures']['room']
    thermometer_configs = settings['configs']

    thermometer = _init_thermometer(settings, intervals)
    relay = _init_relay(settings, args.settings_path)
    # instantiate custom logger
    custom_logger = LogHandler()
    # instantiate loop
    stop = False
    stop_time = intervals['stop_time']
    while True:
        start = time.monotonic()
        current = util.get_now()
        temperature = asyncio.create_task(
            write_temperatures(thermometer, settings_handler)
        )
        if stop and current['datetime'] - stop > stop_time:
            action = asyncio.create_task(
                take_action(settings_handler, current, relay)
            )


    while True:


        # save daily_log if we entered another day
        if check_same_day(last=log['last_day_on'], current=current['day']):
            custom_logger.save_daily_entry(
                log['time_elapsed'],
                log['last_day_on'],
                current['day'],
                paths['daily_log']
            )
