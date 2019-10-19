#!/usr/bin/python3

import json
import RPi.GPIO as GPIO
import signal
import time


relay_pins = [
    {
        'channel': 36,
        'direction': GPIO.OUT,
        'initial': GPIO.HIGH
    }
]

signals = {
    signal.SIGTERM, signal.SIGSEGV, signal.SIGINT
}


class Relay(object):

    def __init__(self, relay_pin):
        '''
        relay_pins is a global list of dicts
        '''

        GPIO.setmode(GPIO.BOARD)

        for relay in relay_pins:

            if relay['channel'] == relay_pin:
                GPIO.setup(**relay)

        self.pin = relay_pin


    def on(self):

        signal.signal.(signal.SIGINT, self.signal_handler)
        signal.signal.(signal.SIGSEGV, self.signal_handler)
        signal.signal.(signal.SIGTERM, self.signal_handler)

        GPIO.output(self.pin, GPIO.LOW)


    def off(self):

        GPIO.output(self.pin, GPIO.HIGH)


    def clean():

        GPIO.cleanup()


    def signal_handler(self, sig_number, sig_handler):

        if sig_number in signals:
            self.clean()


if __name__ == '__main__':

    relay = Relay(36)
    while True
        relay.on()
        # time.sleep(1)
        # relay.off()
        # time.sleep(1)
