#!/usr/bin/python3

import datetime
import json
import logging
import time

from heater_program import Program
from relay import Relay
import settings_handler
import util


logger_name = 'thermostat'
logging.basicConfig(
    format='{levelname:<8} {asctime} - {message}',
    style='{'
)
logger = logging.getLogger(logger_name)
logger.setLevel(logging.DEBUG)


def poll(time_elapsed, heater_switch, current):

    settings = settings_handler.handler(time_elapsed)
    manual_on = settings['manual']
    manual_off = not settings['manual']
    auto_on = settings['auto']
    auto_off = not settings['auto']
    prog_no = settings['program']
    time_to_wait = 5
    logger.debug('time to wait: {}'.format(time_to_wait))

    if manual_on:
        if not heater_switch.stats: # heater is not ON
            heater_switch.on()
        heater_switch.catch_sleep(time_to_wait)
        return time_to_wait

    elif manual_off and auto_on:
        program = Program(settings['program'])
        logger.debug(f"Loaded program {program_number}.")

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

    elif manual_off and auto_off:
        if heater_switch.stats:
            logger.debug("Received signal to turn heater OFF.")
            heater_switch.off()
        time.sleep(time_to_wait)
        return 0


def main():

    heater_switch = Relay('36')
    time_elapsed_r = settings_handler.handler().get('time_elapsed', "0:00:00")
    time_elapsed = datetime.datetime.strptime(time_elapsed_r, "%H:%M:%S")
    time_elapsed = round(datetime.timedelta(
        hours=time_elapsed.hour,
        minutes=time_elapsed.minute,
        seconds=time_elapsed.second
    ).total_seconds())
    last_current = None

    while True:

        # check each loop for when we are in history
        current = util.get_now()

        if last_current is not None and last_current['day'] != current['day']:
            logger.debug('Entered another day in history.')
            util.write_log(
                {
                    "date": "{} {}".format(
                        last_current['weekday'],
                        last_current['formatted_time']
                    ),
                    "time_elapsed": time_elapsed
                }
            )
            time_elapsed = 0

        time_elapsed += poll(
            util.format_seconds(time_elapsed),
            heater_switch,
            current
        )
        last_current = current


if __name__ == '__main__':
    main()
