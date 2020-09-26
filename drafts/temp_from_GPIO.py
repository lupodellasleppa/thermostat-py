#!/usr/bin/python3

import argparse
import RPi.GPIO as GPIO


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s", "--scale",
        help="Choose the temeperature scale.",
        type=str.lower,
        choices=["celsius", "farenheit", "c", "f"],
        required=True
    )
    parser.add_argument(
        "-t", "--temperature",
        help="Choose the desired temperature.",
        type=float,
        required=True
    )

    return parser.parse_args()

def setup_GPIO():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(36, GPIO.OUT)


def read_temp():
    with open('/sys/bus/w1/devices/28-0000046ee84e/w1_slave') as f:
        t = int(f.readlines()[-1].split('=')[-1])/1000

    return t


def to_f(c):
    # farenheit formula (sensor returns celsius by default)
    return c*9/5+32


def switch(l, scale):
    t = read_temp()
    # on returns boolean depending on scale
    on = {
        "celsius": t < l,
        "farenheit": to_f(t) < l
    }
    on = on[scale]
    # 0 turns GPIO ON, so if on == true, not on turns it on
    s = "ON" if on else "OFF"
    GPIO.output(36, not on)
    # "Turned <ON|OFF> @ <TEMPERATURE>°<SCALE>"
    return 'Turned {} @ {}°{}'.format(s, t, scale[0].upper())


def main():
    # setup
    setup_GPIO()
    args = create_parser()
    # scale map
    f_map = {
        "celsius": "celsius",
        "farenheit": "farenheit",
        "c": "celsius",
        "f": "farenheit"
    }
    # switch
    return switch(args.temperature, f_map[args.scale])

if __name__ == '__main__':
    import time

    while(1<2):
        try:
            print(main())
            time.sleep(1)
        except KeyboardInterrupt:
            GPIO.cleanup()
            print("Bye!")
            exit()
