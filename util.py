#!/usr/bin/python3

import datetime
import logging


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
    current_day = days_of_week[current_time.weekday()]
    current_hour = current_time.hour
    current_minute = current_time.minute
    current_second = current_time.second
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
        "total_seconds": current_total_seconds,
        "formatted": str(datetime.timedelta(
            seconds=round(current_total_seconds)
        ))
    }


def five_o(minutes, seconds):
    '''
    Stay on the clock by compensating waiting time.
    '''

    time_to_wait = 300
    # compensate minutes
    to_reach_five = minutes % 5
    time_to_wait -= to_reach_five * 60
    # compensate seconds
    to_reach_sixty = seconds % 60
    time_to_wait -= to_reach_sixty

    return time_to_wait


def program_vs_relay(program_now, heater_switch, time_elapsed):
    '''
    If current day and hour is True in program:
        start and increment time_elapsed
    If otherwise current day and hour is False in program:
        stop and reset time_elapsed
    '''

    if (
         and
        # and heater not on
        not heater_switch.stats
    ):
        # start it
        logger.debug(f"{heater_switch.stats}")
        heater_switch.on()
        logger.debug("Received signal to turn heater ON.")
        time_elapsed += time.time()
    elif (
        not program.program[current['day']][str(current['hours'])] and
        # but heater is on
        heater_switch.stats
    ):
        # stop it
        heater_switch.off()
        logger.debug("Received signal to turn heater OFF.")
        time_elapsed = 0

    return time_elapsed
