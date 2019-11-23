#!/usr/bin/python3

import argparse
import datetime
import json
import logging
import time

from heater_program import Program
from relay import Relay
import settings_handler
import util


def poll(settings_path, time_elapsed, heater_switch, current):

    settings = settings_handler.handler(
        settings_path=args.settings_path,
        settings_changes={
            'time_elapsed': time_elapsed,
            'last_day_on': current['formatted_date']
        }
    )
    logger.debug('Settings handler in poller: {}'.format(settings))
    manual = settings['manual']
    auto = settings['auto']
    prog_no = settings['program']
    time_to_wait = settings['time_to_wait']
    logger.debug('time to wait: {}'.format(time_to_wait))

    if manual:
        if not heater_switch.stats: # heater is not ON
            heater_switch.on()
        heater_switch.catch_sleep(time_to_wait)
        return time_to_wait

    elif auto and not manual:
        program = Program(settings['program'])
        logger.debug(f'Loaded program {program_number}.')

        logger.debug(
            f"It is {current['formatted_time']} on {current['weekday'].title()}."
        )
        # relay vs program relation
        time_elapsed = util.program_vs_relay(
            program.program[current['weekday']][str(current['hours'])],
            heater_switch,
            time_elapsed
        )
        # finally, wait for 5 minutes
        heater_switch.catch_sleep(time_to_wait, time_elapsed)
        return time_to_wait

    elif not manual and not auto:
        if heater_switch.stats:
            logger.debug('Received signal to turn heater OFF.')
            heater_switch.off()
        time.sleep(time_to_wait)
        return 0


def main(settings_path):

    logger_name = 'thermostat'
    logging.basicConfig(
        format='{levelname:<8} {asctime} - {message}',
        style='{'
    )
    logger = logging.getLogger(logger_name)
    logger.setLevel(
        util.get_loglevel(
            settings_handler.load_settings(args.settings_path)['loglevel']
        )
    )

    heater_switch = Relay('36')
    settings = settings_handler.load_settings(settings_path)
    if settings['last_day_on'] != util.get_now()['formatted_date']:
        time_elapsed = 0
        util.write_log(
            {
                'date': last_current['formatted_date'],
                'time_elapsed': time_elapsed
            }
        )
    else:
        time_elapsed_restore = datetime.datetime.strptime(
            settings.get('time_elapsed', '0:00:00'), '%H:%M:%S'
        )
        time_elapsed = round(datetime.timedelta(
        hours=time_elapsed_restore.hour,
        minutes=time_elapsed_restore.minute,
        seconds=time_elapsed_restore.second
    ).total_seconds())
    last_current = None

    while True:

        # check each loop for when we are in history
        current = util.get_now()

        if last_current is not None and last_current['day'] != current['day']:
            logger.debug('Entered another day in history.')
            util.write_log(
                {
                    'date': last_current['formatted_date'],
                    'time_elapsed': time_elapsed
                }
            )
            time_elapsed = 0

        time_elapsed += poll(
            settings_path,
            util.format_seconds(time_elapsed),
            heater_switch,
            current
        )
        last_current = current


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('settings_path')
    args = parser.parse_args()
    main(args.settings_path)
