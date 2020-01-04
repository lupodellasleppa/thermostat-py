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
        # parameters for UDP connection with thermometer
        self.UDP_IP = self.settings['configs']['UDP_IP']
        self.UDP_port = self.settings['configs']['UDP_port']
        self.thermometer_poll = self.settings['poll_intervals']['settings']
        self.thermometer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.thermometer.settimeout(self.thermometer_poll)
        self.thermometer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.temperature = None
        if self.settings['log']['last_day_on'] != util.get_now()['formatted_date']:
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


    def poll(self, current):

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
        prog_no = self.settings['mode']['program']
        self.time_to_wait = self.settings['poll_intervals']['settings']
        logger.debug('time to wait: {}'.format(self.time_to_wait))

        if not self.loop_count or not self.loop_count % self.thermometer_poll:
            self.thermometer.sendto(b'temps_req', (self.UDP_IP, self.UDP_port))
            try:
                self.temperature = json.loads(
                    self.thermometer.recv(4096).decode()
                )['celsius']
            except socket.timeout:
                self.loop_count -= 1
        logger.debug(
            'Temperature from thermometer is: {}° celsius.'.format(
                self.temperature
            )
        )

        if self.temperature < self.settings['mode']['desired_temp']:
            if manual:
                if not self.heater_switch.stats: # heater is not ON
                    self.heater_switch.on()
                self.heater_switch.catch_sleep(
                    self.time_to_wait, self.temperature
                )
                return self.time_to_wait

            elif auto:
                program = Program(self.settings['mode']['program'])
                logger.debug(
                    'Loaded program {}.'.format(program.program_number)
                )
                logger.debug(
                    "It is {} on {}.".format(
                        current['formatted_time'],
                        current['weekday'].title()
                    )
                )
                program_now = program.program[current['weekday']][str(
                    current['hours']
                )]
                logger.debug('Program is now: {}'.format(program_now))
                # program_vs_relay
                if program_now:
                    if not self.heater_switch.stats:
                        # start it
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
                    return self.time_to_wait
                else:
                    if self.heater_switch.stats:
                        # stop it
                        logger.debug('Received signal to turn heater OFF.')
                        self.heater_switch.off()
                    self.heater_switch.catch_sleep(
                        self.time_to_wait, self.temperature
                    )
                    return 0

        else:
            if self.heater_switch.stats:
                logger.debug('Received signal to turn heater OFF.')
                self.heater_switch.off()
            self.heater_switch.catch_sleep(
                self.time_to_wait, self.temperature
            )
            return 0


def main(settings_path):

    heater_poll = Poller(settings_path)

    while True:

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

        heater_poll.time_elapsed += heater_poll.poll(current)
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
