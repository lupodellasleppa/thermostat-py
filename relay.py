#!/usr/bin/python3

import datetime
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

    def __init__(self, pin):
        '''
        Only pin is a necessary argument.

        pin is looked up as relay_pins['channel'], whereas relay_pins
        is a mapping with all other additional information
        [
          {
            'channel': pin,
            'direction': GPIO.<IN|OUT>,
            'initial': GPIO.<LOW|HIGH>
          }
        ]
        '''

        self.pin = pin
        self.stats_path = '/home/pi/raspb-scripts/stats.json'

        GPIO.setmode(GPIO.BOARD)

        if os.path.isfile(self.stats_path):
            self.stats = self.read_stats()[self.pin]
        else:
            self.stats = self.write_stats({self.pin: False})

        for relay in relay_pins:

            if relay['channel'] == int(self.pin):
                GPIO.setup(**relay)


    def on(self):

        stats = self.read_stats()
        if not stats[self.pin]:
            GPIO.output(int(self.pin), GPIO.LOW)

            stats[self.pin] = True

            wrote_stats = self.write_stats(stats)

            if wrote_stats == stats:
                logger.info("Turned ON channel {}.".format(self.pin))
            else:
                logger.warning("Fault while writing stats.")

            self.update_stats(wrote_stats)

        else:
            logger.warning(
                "Channel {} as already set to ON."
                " Shutting down and restarting...".format(self.pin)
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
                logger.info("Turned OFF channel {}.".format(self.pin))
            else:
                logger.warning("Fault while writing stats.")

            self.update_stats(wrote_stats)

        else:
            logger.info("Channel {} was already OFF.".format(self.pin))


    def clean(self):

        GPIO.cleanup(int(self.pin))

        stats = self.read_stats()
        stats[self.pin] = False
        wrote_stats = self.write_stats(stats)

        if wrote_stats == stats:
            logger.info(f"Cleaned up channel {self.pin}.")
            self.update_stats(wrote_stats)

        else:
            logger.warning("Fault while writing stats.")


    def read_stats(self):

        with open(self.stats_path) as f:
            stats = json.load(f)

        return stats


    def write_stats(self, new_stats):
        '''
        Writes new stats to file then reads the file again and returns it.
        '''

        with open(self.stats_path, 'w') as f:
            logger.debug(
                "Wrote {} characters into stats.json file".format(
                    f.write(json.dumps(new_stats))
                )
            )

        return self.read_stats()

    def update_stats(self, new_stats):

        self.stats = new_stats[self.pin]

    def catch_sleep(self, seconds, time_elapsed):
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
                self.clean()
                raise SystemExit
            elif sig_number in usr_signals:
                if time_elapsed:
                    e = time.time()
                    d = e - time_elapsed
                    d = datetime.timedelta(seconds=round(d))
                    logger.info("Heater has been ON for {}".format(str(d)))
                else:
                    logger.info("Heater is OFF.".format(str(d)))

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGSEGV, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGUSR1, signal_handler)

        time.sleep(seconds)
