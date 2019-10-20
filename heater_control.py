#!/usr/bin/python3

import argparse
import datetime
from relay import Relay


def get_max_time():
    '''
    Uses argparse to get desidered time in total_seconds()
    '''

    parser = argparse.ArgumentParser(description='Start heater.')

    parser.add_argument(
        '-H', '--hours',
        help='Number of hours.',
        type=int,
        default=0
    )
    parser.add_argument(
        '-M', '--minutes',
        help='Number of minutes.',
        type=int,
        default=0
    )
    parser.add_argument(
        '-S', '--seconds',
        help='Number of seconds.',
        type=int,
        default=0
    )

    args = parser.parse_args()

    max_time = datetime.timedelta(
        hours=args.hours,
        minutes=args.minutes,
        seconds=args.seconds
    ).total_seconds()

    if not max_time:
        parser.error(
            "Please insert at least one between hours, minutes or seconds."
        )

    return max_time


def turn_heater_on(max_time=3600):
    '''
    Main function to turn the heater on.

    :param max_time: Is the maximum time the heater will be on,
                    after which it will turn itself off automatically.
    '''

    heater_switch = Relay(36)
    heater_switch.on()
    heater_switch.catch_sleep(max_time)
    heater_switch.off()
    heater_switch.clean()


if __name__ == '__main__':

    max_time = get_max_time()
    turn_heater_on(max_time)
