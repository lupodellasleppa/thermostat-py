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

        GPIO.output(self.pin, GPIO.LOW)


    def off(self):

        GPIO.output(self.pin, GPIO.HIGH)


if __name__ == '__main__':

    relay = Relay(36)
    for i in range(3):
        relay.on()
        time.sleep(1)
        relay.off()
        time.sleep(1)
    GPIO.cleanup()
