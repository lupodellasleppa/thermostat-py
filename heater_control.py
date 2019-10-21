#!/usr/bin/python3

import argparse
import datetime
import logging
import time
import util

from heater_program import Program
from relay import Relay


logger_name = 'thermostat'
logging.basicConfig(
    format='{levelname:<8} {asctime} - {message}',
    style='{'
)
logger = logging.getLogger(logger_name)
logger.setLevel(logging.DEBUG)


def get_now():

    current_time = datetime.datetime.now()
    current_day = util.days_of_week[current_time.weekday()]
    current_hour = str(current_time.hour)
    current_minute = str(current_time.minute)
    current_second = str(current_time.second)
    current_total_seconds = datetime.timedelta(
        hours=current_hour,
        minutes=current_minute,
        seconds=current_second
    ).total_seconds()

    return {
        "day": current_day,
        "hours": current_hour,
        "minutes": current_minute,
        "seconds": current_second,
        "total_seconds": current_total_seconds
    }


def turn_heater_on(mode, program_number=0):
    '''
    Main function to turn the heater on.

    :param max_time: Is the maximum time the heater will be on,
                    after which it will turn itself off automatically.
    '''

    assert mode in {'auto', 'manual'}

    heater_switch = Relay('36')

    if mode == 'auto':
        # init the counter for time the heater has been on
        time_elapsed = 0
        while True:
            time_to_wait = 300
            # load program
            program = Program(program_number)
            logger.debug(f"Loaded program {program_number}.")
            # check each loop for when we are in history
            current = get_now()
            logger.debug(
                f"It is { # get formatted current time
                str(datetime.timedelta(seconds=current['total_seconds']))
                } on {current['day']}."
            )
            to_reach_five = current['minutes'] % 5
            to_reach_sixty = current['seconds'] % 60
            if to_reach_five:
                time_to_wait -= to_reach_five * 60
            if to_reach_sixty:
                time_to_wait -= to_reach_sixty
            if ( # if current day and hour is True in program
                program.program[current['day']][current['hours']] and
                # and heater not on
                not heater_switch.stats
            ):
                # start it
                logger.debug(f"{heater_switch.stats}")
                heater_switch.on()
                logger.debug("Received signal to turn heater ON.")
                time_elapsed = time.time()
            elif ( # if otherwise day and hour is False
                not program.program[current['day']][current['hours']] and
                # but heater is on
                heater_switch.stats
            ):
                # stop it
                heater_switch.off()
                logger.debug("Received signal to turn heater OFF.")
                time_elapsed = 0
            # finally, wait for 5 minutes
            heater_switch.catch_sleep(time_to_wait, time_elapsed)
    else:
        while True:
            if not heater_switch.stats:
                heater_switch.on()
            heater_switch.catch_sleep(3600)


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
