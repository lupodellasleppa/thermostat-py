#!/usr/bin/python3

import argparse
import datetime
import json
import logging
import socket
import time

from heater_program import Program
from relay import Relay
import settings_handler
import util


class Poller():

    def __init__(self, settings_path):

        self.settings_path = settings_path
        self.heater_switch = Relay('36')
        # load settings
        self.settings = settings_handler.load_settings(settings_path)
        self.thermometer_poll = self.settings['poll_intervals']['temperature']
        self.time_to_wait = self.settings['poll_intervals']['settings']
        # parameters for UDP communication with thermometer
        self.UDP_IP = self.settings['configs']['UDP_IP']
        self.UDP_port = self.settings['configs']['UDP_port']
        self.thermometer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.thermometer.settimeout(1)
        self.thermometer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.temperature = self.settings['temperatures']['room']
        if (
            self.settings['log']['last_day_on']
            != util.get_now()['formatted_date']
        ):
            self.time_elapsed = 0
            util.write_log(self.settings['log']['global'],
                {
                    'date': self.settings['log']['last_day_on'],
                    'time_elapsed': util.format_seconds(self.time_elapsed)
                }
            )
            self.time_elapsed = 0
        else:
            time_elapsed_restore = datetime.datetime.strptime(
                self.settings['log'].get('time_elapsed', '0:00:00'), '%H:%M:%S'
            )
            self.time_elapsed = round(datetime.timedelta(
            hours=time_elapsed_restore.hour,
            minutes=time_elapsed_restore.minute,
            seconds=time_elapsed_restore.second
        ).total_seconds())

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
        program_number = self.settings['mode']['program']
        desired_temperature = self.settings['mode']['desired_temp']
        logger.debug('time to wait: {}'.format(self.time_to_wait))

        # Get room temperature
        self.temperature = self.request_temperatures()

        # MANUAL MODE
        if manual:
            return self._manual_mode(desired_temperature)

        # AUTO MODE
        elif auto:
            return self._auto_mode(
                desired_temperature, program_number, current
            )

        else: # BOTH MANUAL AND AUTO ARE OFF
            return self.turn_off()


    def _manual_mode(self, desired_temperature):
        '''
        Action to take when MANUAL mode is True

        Manual mode prevails over auto mode and so does desired_temperature
        over what's reported in program.json
        '''

        # Room temperature is lower than desired temperature
        if self.temperature < desired_temperature:
            return self.turn_on()
        # Room temperature satisfies desired temperature
        else:
            return self._turn_off_restart()


    def _auto_mode(self, desired_temperature, program_number, current):
        '''
        Action to take when AUTO mode is True
        '''

        # Load program
        p = self._load_program(program_number, current)

        # Load program setting at current day and time
        program_now = p.program[current['weekday']][str(current['hours'])]
        logger.debug('Program is now: {}'.format(program_now))

        # Value in program is bool and set to True
        if (
            program_now is True
            and self.temperature < desired_temperature
        ):
            return self.turn_on()
        # Value in program is float and greater than actual temperature
        elif (
            util.is_number(program_now) and self.temperature < program_now
        ):
            return self.turn_on()
        # Room temperature satisfies desired temperature
        elif (
            (
                program_now is True
                and self.temperature >= desired_temperature
            ) or (
                util.is_number(program_now) and self.temperature >= program_now
            )
        ):
            return self._turn_off_restart()
        else:
            return self.turn_off()


    def _load_program(self, program_number, current):

        program = Program(program_number)

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


    def _turn_off_restart(self):
        '''
        Catch sleep for at least 180 seconds to prevent quick
        switching on and off of heater
        '''

        seconds = 170
        logger.info(
            'Reached desired temperature.'
            ' Turning off heater and waiting'
            ' {} seconds before next poll.'.format(seconds)
        )

        return self.turn_off(seconds=seconds, reset=True)

    def turn_on(self):

        if not self.heater_switch.stats:
            # Start it
            logger.debug(
                'Heater switch stats: {}'.format(
                    self.heater_switch.stats
                )
            )
            logger.debug('Received signal to turn heater ON.')
            self.heater_switch.on()

        self.heater_switch.catch_sleep(
            self.time_to_wait, self.temperature
        )

        return time.perf_counter() - self.count_start

    def turn_off(self, seconds=None, reset=False):

        if reset:
            self.loop_count = -1

        if seconds is None:
            seconds = self.time_to_wait

        if self.heater_switch.stats:
            # stop it
            logger.debug('Received signal to turn heater OFF.')
            self.heater_switch.off()
            self.heater_switch.catch_sleep(
                seconds, self.temperature
            )
        else:
            self.heater_switch.catch_sleep(
                temperature=self.temperature, seconds=self.time_to_wait
            )

        return 0

    def request_temperatures(self):
        '''
        Send a request for temperatures to ESP8266.
        Response should be a JSON of the type:

        {
          "celsius": float
        }

        If request goes into timeout request is skipped.
        If skips first request so self.temperature is None, repeats the request.
        If request is succesful and new temperature is different than what's
        reported in settings.json file, update the file.
        '''

        logger.info(
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
            util.write_log(heater_poll.settings['log']['global'],
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

    main(args.settings_path)
