#!/usr/bin/python3

import datetime
import json
import logging
import os
import RPi.GPIO as GPIO
import signal
import time

from settings_handler import SettingsHandler


logger_name = 'thermostat.relay'
logger = logging.getLogger(logger_name)


class Relay(object):

    def __init__(self, relay, settings_path):
        '''
        Takes a dictionary containing what GPIO.setup needs as first argument
        plus path to thermostat settings to write relay state at each operation

        relay dict:
        channel, direction {0,1}, initial {0,1}
        '''

        self.pin = str(relay['channel'])
        self.settings_path = settings_path
        if 'state' in relay.keys():
            self.stats = relay.pop('state')
        else:
            self.stats = False
        self.settings_handler = SettingsHandler(self.settings_path)

        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(**relay)

    def on(self):

        if not self.stats:
            GPIO.output(int(self.pin), GPIO.LOW)

            wrote_stats = self.write_stats(True)

            if wrote_stats == True:
                logger.debug(f'Turned ON channel {self.pin}.')
            else:
                logger.warning('Fault while writing stats.')

            self.update_stats(wrote_stats)

        else:
            logger.warning(
                f'Channel {self.pin} was already set to ON.'
                ' Shutting down and restarting...'
            )
            self.off()
            time.sleep(1)
            self.on()

        return self.stats

    def off(self):

        if self.stats:
            GPIO.output(int(self.pin), GPIO.HIGH)

            wrote_stats = self.write_stats(False)

            if wrote_stats == False:
                logger.debug(f'Turned OFF channel {self.pin}.')
            else:
                logger.warning('Fault while writing stats.')

            self.update_stats(wrote_stats)

        else:
            logger.debug(f'Channel {self.pin} was already OFF.')

        return self.stats

    def clean(self):

        GPIO.cleanup(int(self.pin))

        wrote_stats = self.write_stats(False)

        if wrote_stats == False:
            logger.debug(f'Cleaned up channel {self.pin}.')
            self.update_stats(wrote_stats)

        else:
            logger.warning('Fault while writing stats.')

        return self.stats

    def read_stats(self):

        settings = self.settings_handler.load_settings()
        stats = settings['relay']['state']

        return stats

    def write_stats(self, new_stats):
        '''
        Writes new stats to file then reads the file again and returns it.
        '''

        logger.debug("Writing new stats: {}".format(new_stats))
        settings = self.settings_handler.handler(
            settings_changes={
                'relay': {
                    'state': new_stats
                }
            }
        )

        return settings['relay']['state']

    def update_stats(self, new_stats):

        self.stats = new_stats
