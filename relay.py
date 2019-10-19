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

stats_path = '/home/pi/raspb-scripts/stats.json'

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
            self.stats = read_stats()
        else:
            self.stats = write_stats({'relay_state': 'clean'})

        for relay in relay_pins:

            if relay['channel'] == relay_pin:
                GPIO.setup(**relay)

        self.pin = relay_pin

    def on(self):

        if self.stats['relay_state'] != 'on':
            GPIO.output(self.pin, GPIO.LOW)

            self.stats['relay_state'] = 'on'

            if write_stats(self.stats) == self.stats:
                logger.info("Channel {} on.".format(self.pin))
            else:
                logger.warning("Fault while writing stats.")

        else:
            logger.warning(
                "Was already set to on. Shutting down and restarting..."
            )
            self.off()
            catch_sleep(1)
            self.on()

    def off(self):

        if self.stats['relay_state'] != 'off':
            GPIO.output(self.pin, GPIO.HIGH)

            self.stats['relay_state'] = 'off'

            if write_stats(self.stats) == self.stats:
                logger.info("Channel {} off.".format(self.pin))
            else:
                logger.warning("Fault while writing stats.")

        else:
            logger.info("Channel {} was already off.".format(self.pin))

    def clean(self):

        GPIO.cleanup(self.pin)

        self.stats['relay_state'] = 'clean'

        if write_stats(self.stats) == self.stats:
            logger.info("Cleaned up all channels.")
        else:
            logger.warning("Fault while writing stats.")


def read_stats():

    with open(stats_path) as f:
        stats = json.load(f)

    return stats


def write_stats(new_stat):
    '''
    Writes new stats to file then reads the file again and returns it.
    '''

    with open(stats_path, 'w') as f:
        logger.debug(
            "Wrote {} characters into stats.json file".format(
                f.write(json.dumps(new_stat))
            )
        )

    return read_stats()


def signal_handler(sig_number, sig_handler):
    '''
    Signal handler cleans GPIOs on trigger and exits
    '''

    signals = {
        signal.SIGTERM, signal.SIGSEGV, signal.SIGINT
    }

    if sig_number in signals:
        heater_switch.clean()
        raise SystemExit


def catch_sleep(seconds):
    '''
    Wrapper for time.sleep() catching signals.
    '''

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGSEGV, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    time.sleep(seconds)


def turn_heater_on(max_time=3600):
    '''
    Main function to turn the heater on.

    :param max_time: Is the maximum time the heater will be on,
                    after which it will turn itself off automatically.
    '''

    heater_switch.on()
    catch_sleep(max_time)
    heater_switch.clean()

# Needs to be declared in global for signal handling to work
heater_switch = Relay(36)


if __name__ == '__main__':
    import sys

    max_time = 3600

    if len(sys.argv) > 1:
        try:
            max_time = int(sys.argv[1])
        except ValueError as e:
            content = e.args[0]
            invalid = content[content.find(':')+2:]
            raise ValueError(
                "Argument cannot be interpreted as an integer: {}".format(
                    invalid
                )
            )

    turn_heater_on(max_time)
