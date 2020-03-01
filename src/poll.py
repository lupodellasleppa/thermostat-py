#!/usr/bin/python3

import argparse
import datetime
import json
import logging
import logging.handlers
import socket
import time

from program import Program
from relay import Relay
import settings_handler
import util


class Poller():

    def __init__(self, settings_path):

        self.settings_path = settings_path
        # load settings
        self.settings = settings_handler.load_settings(settings_path)
        # arrange paths
        self.program_path = self.settings['paths']['program']
        self.examples_path = self.settings['paths']['examples']
        self.relay_stats_path = self.settings['paths']['relay_stat']
        self.daily_log_path = self.settings['paths']['daily_log']
        # get intervals
        self.thermometer_poll = self.settings['poll_intervals']['temperature']
        self.time_to_wait = self.settings['poll_intervals']['settings']
        # parameters for UDP communication with thermometer
        self.UDP_IP = self.settings['configs']['UDP_IP']
        self.UDP_port = self.settings['configs']['UDP_port']
        self.thermometer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.thermometer.settimeout(1)
        self.thermometer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.temperature = self.settings['temperatures']['room']
        # handle day change
        if (
            self.settings['log']['last_day_on']
            != util.get_now()['formatted_date']
        ):

            self.time_elapsed = 0
            util.write_log(self.daily_log_path,
                {
                    'date': self.settings['log']['last_day_on'],
                    'time_elapsed': util.format_seconds(self.time_elapsed)
                }
            )
            self.time_elapsed = 0

        else:

            time_elapsed_restore = datetime.datetime.strptime(
                self.settings['log'].get('time_elapsed', '0:00:00'),
                '%H:%M:%S'
            )

            self.time_elapsed = round(
                datetime.timedelta(
                    hours=time_elapsed_restore.hour,
                    minutes=time_elapsed_restore.minute,
                    seconds=time_elapsed_restore.second
                ).total_seconds()
            )

        self.program_number = self.settings['mode']['program']

        relay_settings = self.settings['relay']
        self.heater_switch = Relay(relay_settings, self.relay_stats_path)

        self.last_current = None

        self.loop_count = 0

        self.count_start = time.perf_counter()


    def poll(self, current):
        '''
        Poll the settings.json file and behaves accordingly:
         - First sends a request for room temperature if self.loop_count is 0
           or a multiple of self.thermometer_poll (from settings file)
         - If room temperature is lower than desired_temp:
            - First checks if manual is ON
            - Then checks for auto mode

        Returns self.time_to_wait when heater is turned ON, 0 when OFF
        '''

        self.count_start = time.perf_counter()

        self.settings = settings_handler.handler(
            settings_path=self.settings_path,
            settings_changes={
                'log': {
                    'time_elapsed': util.format_seconds(self.time_elapsed),
                    'last_day_on': current['formatted_date']
                }
            }
        )

        logger.debug('Settings handler in poller: {}'.format(self.settings))

        manual = self.settings['mode']['manual']
        auto = self.settings['mode']['auto']
        desired_temperature = self.settings['mode']['desired_temp']
        logger.debug('time to wait: {}'.format(self.time_to_wait))

        return self._handle_on_and_off(current, **self.settings['mode'])

    def _handle_on_and_off(
        self,
        current,
        manual,
        auto,
        program,
        desired_temp
    ):
        '''
        Handles all there is to turning the heater on or off:
        modes, programs, temperature.
        '''

        # Get room temperature
        self.temperature = self.request_temperatures()

        # MANUAL MODE
        if manual:
            return self._manual_mode(desired_temp)

        # AUTO MODE
        elif auto:
            return self._auto_mode(desired_temp, current)

        # BOTH MANUAL AND AUTO ARE OFF
        else:
            return self.turn_off()


    def _manual_mode(self, desired_temperature):
        '''
        Action to take when MANUAL mode is True

        Manual mode prevails over auto mode and so does desired_temperature
        over possible numbers in program.json
        '''

        # Room temperature is lower than desired temperature
        if self.temperature < desired_temperature:
            return self.turn_on()
        # Room temperature satisfies desired temperature
        else:
            return self.turn_off()


    def _auto_mode(self, desired_temperature, current):
        '''
        Action to take when AUTO mode is True
        '''

        # Load program
        p = self._load_program(current)

        # Load program setting at current day and time
        program_now = p.program[current['weekday']][str(current['hours'])]
        logger.debug('Program is now: {}'.format(program_now))

        ### TURN ON CASE
        if (# Value in program is bool, True, and room temp is
            # lower than desired temperature
            (program_now is True and self.temperature < desired_temperature)
            or
            (util.is_number(program_now) and self.temperature < program_now)
        ):
            return self.turn_on()

        ### TURN OFF CASE
        elif (# Value in program is bool, True and room temp is
            # greater than desired temperature
            (program_now is True and self.temperature >= desired_temperature)
            or
            (util.is_number(program_now) and self.temperature >= program_now)
        ):
            return self.turn_off()

        ### ANYTHING ELSE GOES TO OFF, JUST IN CASE
        else:
            return self.turn_off()


    def _load_program(self, current):

        program = Program(
            program_number=self.program_number,
            program_path=self.program_path,
            examples_path=self.examples_path
        )

        logger.debug(
            'Loaded program {}.'.format(program.program_number)
        )
        logger.debug(
            "It is {} on {}.".format(
                current['formatted_time'],
                current['weekday'].title()
            )
        )

        return program

    def turn_on(self):

        seconds = self.time_to_wait

        # only when heater was off at previous loop
        if not self.heater_switch.stats:
            # set seconds to 60 so it doesn't immediately turn back off
            # when temperatures are fluctuating
            seconds = 60
            # reset loop_count so it will read temperatures
            # right away on next loop
            self.loop_count = -1
            logger.info(
                'Room temperature lower than set desired temperature!'
                ' Turning ON heater.'
            )
            logger.debug(
                'Heater switch stats: {}'.format(
                    self.heater_switch.stats
                )
            )
            logger.debug('Received signal to turn heater ON.')
            # start it
            self.heater_switch.on()

        self.heater_switch.catch_sleep(
            seconds, self.temperature
        )

        return time.perf_counter() - self.count_start

    def turn_off(self):

        seconds = self.time_to_wait

        # only when heater was on at previous loop
        if self.heater_switch.stats:
            # set seconds to 170 so it doesn't immediately turn back on
            # when temperatures are fluctuating
            seconds = 170
            # reset loop_count so it will read temperatures
            # right away on next loop
            self.loop_count = -1
            logger.info(
            'Reached desired temperature.'
            ' Turning OFF heater and waiting'
            ' {} seconds before next poll.'.format(seconds)
            )
            logger.debug('Received signal to turn heater OFF.')
            # stop it
            self.heater_switch.off()

        self.heater_switch.catch_sleep(
            seconds, self.temperature
        )

        return 0

    def request_temperatures(self):
        '''
        Send a request for temperatures to ESP8266.
        Response should be a JSON of the type:

        {
          "celsius": float
        }

        If request goes into timeout: request is skipped,
        self.temperature is set to None, request is repeated on next loop.
        If request is succesful and new temperature is different than what's
        reported in settings.json file: update the file and self.temperature.
        '''

        logger.debug(
            'Loop count: {}; thermometer poll: {}; read: {}.'.format(
                self.loop_count,
                self.thermometer_poll,
                not self.loop_count % self.thermometer_poll
            )
        )

        if not self.loop_count or not self.loop_count % self.thermometer_poll:

            self.thermometer.sendto(b'temps_req', (self.UDP_IP, self.UDP_port))

            try:
                self.temperature = json.loads(
                    self.thermometer.recv(4096).decode()
                )['celsius']

                self.loop_count = 0

            except socket.timeout:

                self.loop_count = -1

            if self.temperature != self.settings['temperatures']['room']:

                self.settings = settings_handler.handler(
                    settings_path=self.settings_path,
                    settings_changes={
                        'temperatures': {
                            'room': self.temperature
                        }
                    }
                )

        logger.debug(
            'Temperature from thermometer is: {}° celsius.'.format(
                self.temperature
            )
        )

        return self.temperature


def main(settings_path):

    heater_poll = Poller(settings_path)

    while True:

        start = time.perf_counter()

        # check each loop for when we are in history
        current = util.get_now()

        if (
            heater_poll.last_current is not None and
            heater_poll.last_current['day'] != current['day']
        ):
            logger.info('Entered another day in history.')
            util.write_log(heater_poll.daily_log_path,
                {
                    'date': heater_poll.last_current['formatted_date'],
                    'time_elapsed': util.format_seconds(
                        heater_poll.time_elapsed
                    )
                }
            )
            heater_poll.time_elapsed = 0

        call = time.perf_counter() - start
        heater_poll.time_elapsed += (heater_poll.poll(current) + call)
        heater_poll.loop_count += heater_poll.time_to_wait
        heater_poll.last_current = current


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('settings_path')
    args = parser.parse_args()

    logger_name = 'thermostat'
    logging.basicConfig(
        format='{levelname:<8} {asctime} - {message}',
        style='{'
    )
    logger = logging.getLogger(logger_name)
    logger.setLevel(
        util.get_loglevel(
            settings_handler.load_settings(
                args.settings_path
            )['log']['loglevel']
        )
    )

    # Rotating log file handler, rotates at midnight
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename='/home/pi/thermostat_py/logs/global.log',
        when='midnight',
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    log_format = logging.Formatter(
        fmt='{levelname:<8} {asctime} - {message}',
        style='{'
    )
    file_handler.setFormatter(log_format)
    # add the handler to the logger
    logger.addHandler(file_handler)

    main(args.settings_path)
