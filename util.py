#!/usr/bin/python3

import datetime
import logging
import time


logger_name = 'thermostat'
logging.basicConfig(
    format='{levelname:<8} {asctime} - {message}',
    style='{'
)
logger = logging.getLogger(logger_name)
logger.setLevel(logging.DEBUG)


days_of_week = {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday"
}


def get_now():
    '''
    Get current weekday, hour, minutes, seconds.
    Return them all in a dictionary together with
    total seconds and formatted time.
    '''

    current_time = datetime.datetime.now()
    current_total_seconds = datetime.timedelta(
        hours=current_hour,
        minutes=current_minute,
        seconds=current_second
    ).total_seconds()

    return {
        "day": days_of_week[current_time.weekday()],
        "hours": current_time.hour,
        "minutes": current_time.minute,
        "seconds": current_time.second,
        "microseconds": current_time.microsecond,
        "total_seconds": current_total_seconds,
        "formatted": str(datetime.timedelta(
            seconds=round(current_total_seconds)
        ))
    }


def five_o(minutes, seconds, microseconds):
    '''
    Stay on the clock by compensating waiting time.
    '''

    time_to_wait = 300
    # compensate minutes
    to_reach_five = minutes % 5
    time_to_wait -= to_reach_five * 60
    # compensate seconds
    time_to_wait -= seconds
    # compensate microseconds
    to_reach_thousand -= float(f"0.{microseconds}") 

    return time_to_wait


def program_vs_relay(program_now, heater_switch, time_elapsed):
    '''
    If current day and hour is True in program:
        start and increment time_elapsed
    If otherwise current day and hour is False in program:
        stop and reset time_elapsed
    '''

    if program_now and not heater_switch.stats:
        # start it
        logger.debug(f"{heater_switch.stats}")
        heater_switch.on()
        logger.debug("Received signal to turn heater ON.")
        time_elapsed += time.time()
    elif not program_now and heater_switch.stats:
        # stop it
        heater_switch.off()
        logger.debug("Received signal to turn heater OFF.")
        time_elapsed = 0

    return time_elapsed
