#!/usr/bin/python3

import argparse
import asyncio
import datetime
import logging
import signal
# import socket
import time

# from iottly_sdk import IottlySDK
from exceptions import *
from log_handler import LogHandler
from program import Program
from relay import Relay
from settings_handler import SettingsHandler
from thermometer import ThermometerLocal
import util


# utilities strictly related to this module

def _create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("settings_path")
    args = parser.parse_args()
    return args

# module inits

def _init_loghandler(log_path):
    return LogHandler(log_path)

def _init_program(program_number, paths):
    return Program(
        program_number=program_number,
        program_path=paths["program"],
        examples_path=paths["examples"]
    )

def _init_relay(settings, settings_path):
    return Relay(settings["relay"], settings_path)

def _init_thermometer(settings, intervals):
    thermometer_ip, thermometer_port = settings["configs"]
    return ThermometerLocal(
        settings["configs"]["UDP_IP"],
        settings["configs"]["UDP_port"],
        intervals["temperature"]
    )

# settings file interfacing
def _load_settings(settings_handler):
    """
    Loads informations that change in settings_file at every loop.
    Returns a flat dict similar to the settings_file.
    """
    settings = settings_handler.load_settings()
    mode = settings["mode"]
    manual = mode["manual"]
    auto = mode["auto"]
    program_number = mode["program"]
    desired_temp = mode["desired_temp"]
    room_temperature = settings["temperatures"]["room"]
    relay_state = settings["relay"]["state"]
    last_day_on = settings["log"]["last_day_on"]
    time_elapsed = settings["log"]["time_elapsed"]
    return {
        "mode": mode,
        "manual": manual,
        "auto": auto,
        "program_number": program_number,
        "desired_temp": desired_temp,
        "room_temperature": room_temperature,
        "relay_state": relay_state,
        "last_day_on": last_day_on,
        "time_elapsed": time_elapsed
    }

async def _write_temperatures(
    thermometer, settings_handler, known_temperature
):
    """
    Asks the thermometer for current temperature.
    Writes the new value to settings_file.
    Returns exception on failure.
    Does nothing if recevied temperature is same as last reading from
    settings_file.
    """
    try:
        received_temperature = await thermometer.request_temperatures()
        logger.debug("Received temperature: {}".format(received_temperature))
    except ThermometerTimeout as e:
        logger.error("Could not retrieve temperatures from themometer.")
        return e
    if received_temperature != known_temperature:
        settings_handler.handler(
            {"temperatures": {"room": received_temperature}}
        )

# action
def _handle_on_and_off(
        current,
        paths,
        relay,
        manual,
        auto,
        program_number,
        desired_temp,
        room_temperature
    ):
    """Handles all there is to turning the heater on or off.
    NOTE: relay module writes relay state to settings_file
    at every call of on() or off() methods.
    No need to rewrite that in this module."""
    # MANUAL MODE
    if manual:
        return _manual_mode(desired_temp, room_temperature, relay)
    # AUTO MODE
    elif auto:
        return _auto_mode(
            current, desired_temp, paths, program_number, relay, room_temperature
        )
    # BOTH MANUAL AND AUTO ARE OFF
    else:
        return relay.off()

def _manual_mode(desired_temperature, room_temperature, relay):
    """
    Action to take when MANUAL mode is True.
    Manual mode prevails over auto mode and so does desired_temperature
    over numeric values in program.json
    """
    # Room temperature is lower than desired temperature
    if room_temperature < desired_temperature and not relay.stats:
        return relay.on()
    # Room temperature satisfies desired temperature
    else:
        return relay.off()

def _auto_mode(
    current,
    desired_temp,
    paths,
    program_number,
    relay,
    room_temperature
):
    # load program
    program = _init_program(program_number, paths)
    # load program setting at current day and time
    program_now = program.program[current["weekday"]][str(current["hours"])]
    ### TURN ON CASE
    if (# Value in program is bool
        (program_now is True and room_temperature < desired_temp)
        or
        # value in program is float
        (util.is_number(program_now) and room_temperature < program_now)
        and not relay.stats
    ):
        return relay.on()
    ### TURN OFF CASE
    elif (# Value in program is bool
        (program_now is True and room_temperature >= desired_temp)
        or
        (util.is_number(program_now) and room_temperature >= program_now)
        and not relay.stats
    ):
        return relay.off()

    ### ANYTHING ELSE GOES TO OFF, JUST IN CASE
    else:
        return relay.off()

async def main():
    args = _create_parser()
    # load settings
    settings_handler = SettingsHandler(args.settings_path)
    settings = settings_handler.load_settings()
    log = settings["log"]
    mode = settings["mode"]
    paths = settings["paths"]
    intervals = settings["intervals"]
    relay_configs = settings["relay"]
    room_temperature = settings["temperatures"]["room"]
    thermometer_configs = settings["configs"]
    # init logger
    logger_name = 'thermostat'
    logging.basicConfig(
        format='{levelname:<8} {asctime} - {message}',
        style='{'
    )
    global logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(util.get_loglevel(log["loglevel"]))
    # init modules
    custom_logger = _init_loghandler(paths["daily_log"])
    relay = _init_relay(settings, args.settings_path)
    thermometer = _init_thermometer(settings, intervals)
    # instantiate loop
    last_relay_state = relay.stats
    last_mode = mode
    stop = False
    stop_time = intervals["stop_time"]
    time_elapsed = 0
    # signal handling
    def signal_handler(sig_number, sig_handler):
        off_signals = {
            signal.SIGTERM, signal.SIGSEGV, signal.SIGINT
        }

        usr_signals = {
            signal.SIGUSR1
        }

        if sig_number in off_signals:
            logger.info("{} received, shutting down...".format(sig_number))
            relay.off()
            relay.clean()
            exit()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGSEGV, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # start loop
    logger.info("Starting loop. Settings:\n{}".format(settings))
    while(1<2):
        # initialize states
        action = False
        start = time.monotonic()
        # update current time and values from settings_file
        current = util.get_now()
        updated_settings = _load_settings(settings_handler)
        # log if day_changed
        day_changed = util.check_same_day(
            updated_settings["last_day_on"], current["formatted_date"]
        )
        if day_changed:
            custom_logger.save_daily_entry(
                log["time_elapsed"],
                log["last_day_on"]
            )
        # create async tasks
        logger.debug("Asking temperature to thermometer...")
        temperature = asyncio.create_task(
            _write_temperatures(
                thermometer,
                settings_handler,
                updated_settings["room_temperature"]
            )
        )
        if not updated_settings["room_temperature"]:
            temperature = await temperature
            # if no value for room_temperature and read from thermometer
            # fails, retry endlessly without taking any other action
            if isinstance(temperature, ThermometerTimeout):
                continue
        # stop for given time in settings_file when relay_state changes
        if updated_settings["relay_state"] != last_relay_state:
            stop = current["datetime"]
            logger.info("Stop at {}.".format(stop))
        last_relay_state = updated_settings["relay_state"]
        # but cancel stop if settings changes
        for k, v in last_mode.items():
            if updated_settings[k] != v:
                stop = False
                break
        last_mode = {
            "manual": updated_settings["manual"],
            "auto": updated_settings["auto"],
            "program": updated_settings["program"],
            "desired_temp": updated_settings["desired_temp"]
        }
        # check if stop is expired
        if stop:
            stop_expired = util.stop_expired(current, stop, stop_time)
        # do stuff if there's no stop or if stop is expired
        if not stop or stop_expired:
            action = _handle_on_and_off(
                current,
                paths,
                relay,
                **{
                    k: v for k, v in updated_settings.items()
                    if k in _handle_on_and_off.__code__.co_varnames
                }
            )
            logger.info("Relay state: {}".format(action))
        # retrieve new_settings from UI and loop and write them to file
        new_settings = {}
        # TODO: new_settings = _receive_settings_updates()
        # new_settings.update({
        #
        # })
        if action:
            time_elapsed_restore = datetime.datetime.strptime(
                updated_settings.get('time_elapsed', '0:00:00'),
                '%H:%M:%S'
            )
            time_elapsed = datetime.timedelta(
                hours=time_elapsed_restore.hour,
                minutes=time_elapsed_restore.minute,
                seconds=time_elapsed_restore.second
            ).total_seconds()
            time_elapsed += round(time.monotonic() - start)
            time_elapsed = util.format_seconds(time_elapsed)
        if day_changed or time_elapsed:
            new_settings.update({
                "log": {
                    "time_elapsed": time_elapsed,
                    "last_day_on": current["formatted_date"]
                }
            })
        if new_settings:
            # write only if there's a difference
            # (even if this is already managed by SettingsHandler)
            settings_handler.handler(new_settings)
        time.sleep(intervals["settings"])

if __name__ == '__main__':
    asyncio.run(main())
temperature
