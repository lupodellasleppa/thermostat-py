#!/usr/bin/python3

import json
import logging
import os
import RPi.GPIO as GPIO
import signal
import time


logger_name = 'thermostat'
logging.basicConfig(
    format='{levelname:<8} {asctime} - {message}',
    style='{'
)
logger = logging.getLogger(logger_name)
logger.setLevel(logging.INFO)

relay_pins = [
    {
        'channel': 36,
        'direction': GPIO.OUT,
        'initial': GPIO.HIGH
    }
]


class Relay(object):

    def __init__(self, relay_pin):
        '''
        relay_pins is a global list of dicts
        '''

        GPIO.setmode(GPIO.BOARD)

        if os.path.isfile(stats_path):
            self.stats = self.read_stats()
        else:
            self.stats = self.write_stats({'relay_state': 'clean'})

        for relay in relay_pins:

            if relay['channel'] == relay_pin:
                GPIO.setup(**relay)

        self.pin = relay_pin
        self.stats_path = '/home/pi/raspb-scripts/stats.json'

    def on(self):

        if self.stats['relay_state'] != 'on':
            GPIO.output(self.pin, GPIO.LOW)

            self.stats['relay_state'] = 'on'

            if self.write_stats(self.stats) == self.stats:
                logger.info("Channel {} on.".format(self.pin))
            else:
                logger.warning("Fault while writing stats.")

        else:
            logger.warning(
                "Was already set to on. Shutting down and restarting..."
            )
            self.off()
            self.catch_sleep(1)
            self.on()

    def off(self):

        if self.stats['relay_state'] != 'off':
            GPIO.output(self.pin, GPIO.HIGH)

            self.stats['relay_state'] = 'off'

            if self.write_stats(self.stats) == self.stats:
                logger.info("Channel {} off.".format(self.pin))
            else:
                logger.warning("Fault while writing stats.")

        else:
            logger.info("Channel {} was already off.".format(self.pin))

    def clean(self):

        GPIO.cleanup(self.pin)

        self.stats['relay_state'] = 'clean'

        if self.write_stats(self.stats) == self.stats:
            logger.info("Cleaned up all channels.")
        else:
            logger.warning("Fault while writing stats.")


    def read_stats(self, ):

        with open(self.stats_path) as f:
            stats = json.load(f)

        return stats


    def write_stats(self, new_stat):
        '''
        Writes new stats to file then reads the file again and returns it.
        '''

        with open(self.stats_path, 'w') as f:
            logger.debug(
                "Wrote {} characters into stats.json file".format(
                    f.write(json.dumps(new_stat))
                )
            )

        return self.read_stats()


    def signal_handler(self, sig_number, sig_handler):
        '''
        Signal handler cleans GPIOs on trigger and exits
        '''

        signals = {
            signal.SIGTERM, signal.SIGSEGV, signal.SIGINT
        }

        if sig_number in signals:
            self.clean()
            raise SystemExit


    def catch_sleep(self, seconds):
        '''
        Wrapper for time.sleep() catching signals.
        '''

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGSEGV, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        time.sleep(seconds)
