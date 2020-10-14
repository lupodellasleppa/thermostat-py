#!/usr/bin/python3

import argparse
import asyncio
import datetime
import json
import logging
import os
import signal
# import socket
import threading
import time

import flask
from iottly_sdk import IottlySDK

from exceptions import *
from log_handler import LogHandler
from program import Program
from relay import Relay
from settings_handler import SettingsHandler
from thermometer import ThermometerLocal, ThermometerDirect
import util


# utilities strictly related to this module
def _create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("settings_path")
    args = parser.parse_args()
    return args


def _retrieve_iottly_info(iottly_path):
    """
    Returns iottly project ID and device UUID from settings
    """
    iottly_settings_path = os.path.join(
        iottly_path, "etc", "iottly", "settings.json"
    )
    with open(iottly_settings_path) as f:
        iottly_settings = json.load(f)
    project_id = iottly_settings["IOTTLY_PROJECT_ID"]
    device_id = iottly_settings["IOTTLY_MQTT_DEVICE_USER"]
    return project_id, device_id

# iottlySDK functions

def on_agent_status_changed(status):
    logger.warning('iottly agent status: {}'.format(status))


def on_connection_status_changed(status):
    logger.warning('iottly agent mqtt status: {}'.format(status))


# module inits

class WSDK(IottlySDK):
    def _process_msg_from_agent(self, msg):
        logger.info("MSG FROM AGENT: {}".format(msg))
        super()._process_msg_from_agent(msg)


def _init_iottly_sdk():
    iottly_sdk = WSDK(
        name='thermostat-py',
        max_buffered_msgs=100,
        on_agent_status_changed=on_agent_status_changed,
        on_connection_status_changed=on_connection_status_changed
    )
    iottly_sdk.start()
    return iottly_sdk


def _init_loghandler(log_path):
    return LogHandler(log_path)


def _init_program(program, paths):
    return Program(
        program_number=program,
        program_path=paths["program"],
        examples_path=paths["examples"]
    )


def _init_relay(settings, settings_path):
    return Relay(settings, settings_path)


def _init_thermometer(settings, intervals):
    if settings['direct']:
        return ThermometerDirect()
    else:
        thermometer_ip, thermometer_port = settings["configs"]
        return ThermometerLocal(
            settings["UDP_IP"],
            settings["UDP_port"],
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
    program = mode["program"]
    desired_temp = mode["desired_temp"]
    room_temperature = settings["temperatures"]["room"]
    relay_state = settings["relay"]["state"]
    last_day_on = settings["log"]["last_day_on"]
    time_elapsed = settings["log"]["time_elapsed"]
    return {
        "mode": mode,
        "manual": manual,
        "auto": auto,
        "program": program,
        "desired_temp": desired_temp,
        "room_temperature": room_temperature,
        "relay_state": relay_state,
        "last_day_on": last_day_on,
        "time_elapsed": time_elapsed
    }

# action

async def _handle_on_and_off(
        current,
        relay,
        paths,
        manual,
        auto,
        program,
        desired_temp,
        room_temperature
    ):
    """Handles all there is to turning the heater on or off.
    NOTE: relay module writes relay state to settings_file
    at every call of on() or off() methods.
    No need to rewrite that in this module."""
    logger.debug("called action func")
    # MANUAL MODE
    if manual:
        logger.debug("manual of _handle_on_and_off")
        return _manual_mode(desired_temp, room_temperature, relay)
    # AUTO MODE
    elif auto:
        logger.debug("auto of _handle_on_and_off")
        return _auto_mode(
            current, desired_temp, paths, program, relay, room_temperature
        )
    # BOTH MANUAL AND AUTO ARE OFF
    else:
        logger.debug("else of _handle_on_and_off")
        return relay.off()


def _manual_mode(desired_temperature, room_temperature, relay):
    """
    Action to take when MANUAL mode is True.
    Manual mode prevails over auto mode and so does desired_temperature
    over numeric values in program.json
    """
    # Room temperature is lower than desired temperature
    if room_temperature < desired_temperature:
        if not relay.stats:
            return relay.on()
        else:
            return relay.stats
    # Room temperature satisfies desired temperature
    else:
        return relay.off()


def _auto_mode(
    current,
    desired_temp,
    paths,
    program,
    relay,
    room_temperature
):
    # load program
    program = _init_program(program, paths)
    # load program setting at current day and time
    program_now = program.program[current["weekday"]][str(current["hours"])]
    ### TURN ON CASE
    if (# Value in program is bool
        (program_now is True and room_temperature < desired_temp)
        or
        # value in program is float
        (util.is_number(program_now) and room_temperature < program_now)
    ):
        if not relay.stats:
            return relay.on()
        else:
            return relay.stats
    ### TURN OFF CASE
    else:
        return relay.off()

# main

class Thermostat():
    def __init__(self, exit):
        self.exit = exit
        args = _create_parser()
        self.settings_handler = SettingsHandler(args.settings_path)
        self.settings = self._load_settings()
        iottly_path = self.settings["paths"]["iottly"]
        self.project_id, self.device_id = _retrieve_iottly_info(iottly_path)
        self._init_logger()
        self._init_modules()
        self.send_stuff_counter = False
        self.time_since_start = 0
        self.iottly_sdk.subscribe(
            cmd_type="send_stuff",
            callback=self._send_stuff
        )

    def _load_settings(self):
        settings = self.settings_handler.load_settings()
        return {
            "log": settings["log"],
            "mode": settings["mode"],
            "manual": settings["mode"]["manual"],
            "auto": settings["mode"]["auto"],
            "program": settings["mode"]["program"],
            "desired_temp": settings["mode"]["desired_temp"],
            "paths": settings["paths"],
            "intervals": settings["intervals"],
            "relay_configs": settings["relay"],
            "room_temperature": settings["temperatures"]["room"],
            "thermometer_configs": settings["configs"],
            "log": settings["log"]
        }

    def _init_logger(self):
        logger_name = 'thermostat'
        logging.basicConfig(
            format='{levelname:<8} {asctime} - {message}',
            style='{'
        )
        global logger
        logger = logging.getLogger(logger_name)
        logger.setLevel(
            util.get_loglevel(
                self.settings["log"]["loglevel"]
            )
        )

    def _init_modules(self):
        self.custom_logger = _init_loghandler(
            self.settings["paths"]["daily_log"]
        )
        self.relay = _init_relay(
            self.settings["relay_configs"],
            self.settings_handler
        )
        self.thermometer = _init_thermometer(
            self.settings["thermometer_configs"],
            self.settings["intervals"]
        )
        self.iottly_sdk = _init_iottly_sdk()

    def _send_stuff(self, cmdpars):
        logger.info("Received from iottly: {}".format(cmdpars))
        self.send_stuff_counter = int(cmdpars["send_every"])

    async def loop(self):
        last_relay_state = self.relay.stats
        last_mode = self.settings["mode"]
        stop = False
        cycle_count = 0
        stop_time = self.settings["intervals"]["stop_time"]
        time_elapsed = 0
        time_after_sleep = 0
        # start loop
        logger.info("Starting loop. Settings:\n{}".format(self.settings))
        while not self.exit.is_set():
            # initialize states
            action = False
            start = time.monotonic()
            # update current time and values from settings_file
            current = util.get_now()
            updated_settings = self._load_settings()
            # send stuff to iottly
            if self.send_stuff_counter:
                if not cycle_count % self.send_stuff_counter:
                    self.iottly_sdk.call_agent('send_message', {
                        "manual": updated_settings["manual"],
                        "auto": updated_settings["auto"],
                        "program": updated_settings["program"],
                        "desired_temp": updated_settings["desired_temp"],
                        "relay": updated_settings["relay_configs"]["state"],
                        "room_temperature": updated_settings["room_temperature"]
                    })
                cycle_count += 1
            else:
                cycle_count = 0
            # log if day_changed
            day_changed = util.check_same_day(
                updated_settings["log"]["last_day_on"],
                current["formatted_date"]
            )
            if day_changed:
                self.custom_logger.save_daily_entry(
                    updated_settings["log"]["time_elapsed"],
                    updated_settings["log"]["last_day_on"]
                )
            # create async tasks
            logger.debug("Asking temperature to thermometer...")
            request_temperatures = asyncio.create_task(
                self.thermometer.request_temperatures()
            )
            if not updated_settings["room_temperature"]:
                try:
                    temperature = await temperature
                # if no value for room_temperature and read from thermometer
                # fails, retry endlessly without taking any other action
                except ThermometerTimeout:
                    time.sleep(intervals["settings"])
                    continue
            # stop for given time in settings_file when relay_state changes
            if updated_settings["relay_configs"]["state"] != last_relay_state:
                stop = current["datetime"]
                logger.info("Stop at {}.".format(stop))
            last_relay_state = updated_settings["relay_configs"]["state"]
            # but cancel stop if settings changes
            for k, v in last_mode.items():
                if updated_settings[k] != v:
                    stop = False
                    break
            # update last_mode
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
                action_task = asyncio.create_task(_handle_on_and_off(
                    current, self.relay, **{
                        k: v for k, v in updated_settings.items()
                        # unpacks only for params in func signature
                        if k in _handle_on_and_off.__code__.co_varnames
                    }
                ))
            # retrieve new_settings from UI and loop and write them to file
            new_settings = {}
            logger.debug("Just before await of temp")
            try:
                received_temperature = await request_temperatures
                logger.info(
                    "Received temperature: {}".format(received_temperature)
                )
                if (
                    received_temperature !=
                    updated_settings["room_temperature"]
                ):
                    self.settings_handler.handler(
                        {"temperatures": {"room": received_temperature}}
                    )
            except ThermometerTimeout as e:
                logger.warning(
                    "Could not retrieve temperatures from themometer."
                )
                pass
            logger.debug("Just before await of action")
            action = await action_task
            logger.info("Relay state: {}".format(action))

            # FINISHED ACTION: sleep then update settings

            # interval is X we need to sleep for
            # X - time spent until now
            # otherwise we will sleep for more than X
            time_to_sleep = (
                self.settings["intervals"]["settings"] -
                (time.monotonic() - start)
            )
            time.sleep(max(0, time_to_sleep - time_after_sleep))
            after_sleep = time.monotonic()
            time_after_sleep = 0

            # update elapsed time with heater on
            if action:
                self.time_since_start += time.monotonic() - start
            logger.info("time_since_start: {}".format(self.time_since_start))
            time_elapsed = 0
            time_to_add = int(self.time_since_start)
            self.time_since_start -= time_to_add
            # self.time_since_start goes "backwards"
            # so we need to reset it sometimes
            if not time_to_add:
                time_to_add = round(self.time_since_start)
                self.time_since_start = 0
            if time_to_add:
                time_elapsed = util.increment_time_elapsed(
                    updated_settings, time_to_add
                )
                logger.info("time_elapsed: {}".format(time_elapsed))
            # update settings
            if day_changed:
                new_settings.update({
                    "log": {
                        "time_elapsed": "0:00:00",
                        "last_day_on": current["formatted_date"]
                    }
                })
            if time_elapsed:
                new_settings.update({
                    "log": {
                        "time_elapsed": time_elapsed
                    }
                })
            if new_settings:
                # write only if there's a difference
                # (even if this is already managed by SettingsHandler)
                self.settings_handler.handler(new_settings)
            time_after_sleep = time.monotonic() - after_sleep
        # raise UnknownException('Exited main loop.')
        self.relay.off()
        self.relay.clean()


def main():
    thermostat_exit = threading.Event()
    thermostat = Thermostat(thermostat_exit)

    app = flask.Flask(__name__)

    app.logger = logger

    @app.route(
        '/project/<projectID>/device/<deviceID>/command',
        methods=["POST"]
    )
    def send_to_sdk(projectID, deviceID):
        cmd_type, values = flask.request.json.values()
        values = {k.split(".")[1]: v for k, v in values.items()}
        data = {"data": {cmd_type: values}}
        # data["data"] = flask.request.json
        data = json.dumps(data)
        logger.info("flask data: {}".format(data))
        try:
            thermostat.iottly_sdk._process_msg_from_agent(data)
            return ("", 200)
        except:
            return

    def run_thermostat():
        asyncio.run(thermostat.loop())

    thermostat_loop = threading.Thread(
        target=run_thermostat, name='thermostat-loop'
    )

    # signal handling
    def signal_handler(sig_number, sig_handler):
        off_signals = {
            signal.SIGTERM, signal.SIGSEGV, signal.SIGINT
        }
        usr_signals = {
            signal.SIGUSR1, signal.SIGHUP
        }
        if sig_number in off_signals:
            logger.info("{} received, shutting down...".format(sig_number))
            thermostat_exit.set()
            exit()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGSEGV, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGUSR1, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)

    try:
        # start the flask server for local APIs
        thermostat_loop.start()
        app.run()
    except Exception as e:
        thermostat.relay.clean()
        logger.exception(e)
        raise UnknownException(e)

if __name__ == '__main__':
    main()
