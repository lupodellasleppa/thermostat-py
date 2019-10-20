#!/usr/bin/python3

import argparse
import datetime
from heater_program import Program
import logging
from relay import Relay
import util


logger_name = 'thermostat'
logging.basicConfig(
    format='{levelname:<8} {asctime} - {message}',
    style='{'
)
logger = logging.getLogger(logger_name)
logger.setLevel(logging.INFO)


def get_now():

    current_time = datetime.datetime.now()
    current_day = util.days_of_week[current_time.weekday()]
    current_hour = str(current_time.hour)

    return current_day, current_hour


def turn_heater_on(mode, program_number=0):
    '''
    Main function to turn the heater on.

    :param max_time: Is the maximum time the heater will be on,
                    after which it will turn itself off automatically.
    '''

    assert mode in {'auto', 'manual'}

    heater_switch = Relay('36')

    if mode == 'auto':
        while True:
            # load program
            program = Program(program_number)
            # check each loop for when we are in history
            current_day, current_hour = get_now()
            if ( # if current day and hour is True in program
                program.program[current_day][current_hour] and
                # and heater not on
                not heater_switch.stats
            ):
                # start it
                heater_switch.on()
            elif ( # if otherwise day and hour is False
                not program.program[current_day][current_hour] and
                # but heater is on
                heater_switch.stats
            ):
                # stop it
                heater_switch.off()
            # finally, wait for 5 minutes
            heater_switch.catch_sleep(300)
    else:
        while True:
            if not heater_switch.stats:
                heater_switch.on()
            heater_switch.catch_sleep(300)


def main():

    parser = argparse.ArgumentParser(
        description=(
            'Start heater according to mode and program number'
            ' if mode is auto.'
        )
    )

    parser.add_argument(
        'mode',
        help='Heater mode [auto|manual].',
        type=str,
        default='auto'
    )

    parser.add_argument(
        'program',
        help='Program number to start.',
        type=str,
        nargs='?'
    )

    args = parser.parse_args()

    if args.mode == 'auto' and args.program is None:
        raise argparse.error(
            "A program number must be specified if run in auto mode."
        )

    turn_heater_on(args.mode, args.program)


if __name__ == '__main__':

    main()
