#!/usr/bin/python3

import datetime
import json
import logging
import os
import RPi.GPIO as GPIO
import signal
import time


logger_name = 'thermostat.relay'
logger = logging.getLogger(logger_name)


class Relay(object):

    def __init__(self, relay, path):
        '''
        Takes a dictionary containing what GPIO.setup needs:
        channel, direction {0,1}, initial {0,1},
        and a path where to store the state of the relay
        '''

        self.pin = str(relay['channel'])
        self.stats_path = path

        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(**relay)

        # read initial stats from file if any
        if os.path.isfile(self.stats_path):
            self.stats = self.read_stats()[self.pin]
        # otherwise init them to False
        else:
            self.stats = self.write_stats({self.pin: False})

    def on(self):

        stats = self.read_stats()
        if not stats[self.pin]:
            GPIO.output(int(self.pin), GPIO.LOW)

            stats[self.pin] = True

            wrote_stats = self.write_stats(stats)

            if wrote_stats == stats:
                logger.info(f'Turned ON channel {self.pin}.')
            else:
                logger.warning('Fault while writing stats.')

            self.update_stats(wrote_stats)

        else:
            logger.warning(
                f'Channel {self.pin} was already set to ON.'
                ' Shutting down and restarting...'
            )
            self.off()
            self.catch_sleep(1)
            self.on()


    def off(self):

        stats = self.read_stats()
        if stats[self.pin]:
            GPIO.output(int(self.pin), GPIO.HIGH)

            stats[self.pin] = False
            wrote_stats = self.write_stats(stats)

            if wrote_stats == stats:
                logger.info(f'Turned OFF channel {self.pin}.')
            else:
                logger.warning('Fault while writing stats.')

            self.update_stats(wrote_stats)

        else:
            logger.info(f'Channel {self.pin} was already OFF.')


    def clean(self):

        GPIO.cleanup(int(self.pin))

        stats = self.read_stats()
        stats[self.pin] = False
        wrote_stats = self.write_stats(stats)

        if wrote_stats == stats:
            logger.info(f'Cleaned up channel {self.pin}.')
            self.update_stats(wrote_stats)

        else:
            logger.warning('Fault while writing stats.')


    def read_stats(self):

        with open(self.stats_path) as f:
            stats = json.load(f)

        return stats


    def write_stats(self, new_stats):
        '''
        Writes new stats to file then reads the file again and returns it.
        '''

        with open(self.stats_path, 'w') as f:
            n = f.write(json.dumps(new_stats))
            logger.debug(f'Wrote {n} characters into stats.json file')

        return self.read_stats()

    def update_stats(self, new_stats):

        self.stats = new_stats[self.pin]

    def catch_sleep(self, seconds, temperature):
        '''
        Wrapper for time.sleep() catching signals.
        '''

        def signal_handler(sig_number, sig_handler):
            '''
            Signal handler cleans GPIOs on trigger and exits
            '''

            off_signals = {
                signal.SIGTERM, signal.SIGSEGV, signal.SIGINT
            }

            usr_signals = {
                signal.SIGUSR1
            }

            if sig_number in off_signals:
                self.off()
                logger.debug(f'Turned off channel {self.pin}')
                self.clean()
                logger.debug(f'Cleaned channel {self.pin}')
                raise SystemExit
            elif sig_number in usr_signals:
                logger.info(
                    'Room temperature is {}° celsius.'.format(temperature)
                )

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGSEGV, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGUSR1, signal_handler)

        time.sleep(seconds)
