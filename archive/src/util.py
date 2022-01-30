#!/usr/bin/python3

import datetime
import json
import logging
import os
import time

from exceptions import *


logger_name = 'thermostat'
logger = logging.getLogger(logger_name)

days_of_week = {
    0: 'monday',
    1: 'tuesday',
    2: 'wednesday',
    3: 'thursday',
    4: 'friday',
    5: 'saturday',
    6: 'sunday'
}


def get_loglevel(level):

    loglevel = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }

    return loglevel[level.lower()]


def get_now():
    '''
    Get current weekday, hour, minutes, seconds.
    Return them all in a dictionary together with
    total seconds and formatted time.
    '''
    current_time = datetime.datetime.now()
    current_weekday = days_of_week[current_time.weekday()]
    current_day = current_time.day
    current_hour = current_time.hour
    current_minute = current_time.minute
    current_second = current_time.second
    current_microsecond = current_time.microsecond
    current_total_seconds = datetime.timedelta(
        hours=current_hour,
        minutes=current_minute,
        seconds=current_second
    ).total_seconds()
    current_date = str(current_time.date())

    return {
        'datetime': current_time,
        'day': current_day,
        'weekday': current_weekday,
        'hours': current_hour,
        'minutes': current_minute,
        'seconds': current_second,
        'microseconds': current_microsecond,
        'total_seconds': current_total_seconds,
        'formatted_time': str(datetime.timedelta(
            seconds=round(current_total_seconds)
        )),
        'formatted_date': current_date
    }


def write_log(log_path, data):
    if not os.path.isfile(log_path) or not os.stat(log_path).st_size:
        with open(log_path, 'w') as f:
            f.write(json.dumps([data], indent=2))
            f.write('\n')
    else:
        with open(log_path) as f:
            log_file = json.load(f)
        log_file.append(data)
        with open(log_path, 'w') as f:
            f.write(json.dumps(log_file, indent=2))
            f.write('\n')

    return 'Wrote log to file.'


def format_seconds(seconds):
    '''
    Takes a quantity of seconds (can be float) as parameter,
    rounds it, and returns a formatted string of the kind
    H:mm:SS
    '''
    return str(datetime.timedelta(
        seconds=round(seconds)
    ))


def five_o(time_to_wait, minutes=0, seconds=0, microseconds=0):
    '''
    Stay on the clock by compensating waiting time.
    '''
    if minutes:
        # compensate minutes
        to_reach_five = minutes % 5
        time_to_wait -= to_reach_five * 60
    if seconds:
        # compensate seconds
        time_to_wait -= seconds
    if microseconds:
        # compensate microseconds
        time_to_wait -= float(f'0.{microseconds:0>6}')

    return time_to_wait


def is_number(presumed_number):
    '''
    Return true if given param is a number (int or float)
    '''
    is_int = isinstance(presumed_number, int)
    is_float = isinstance(presumed_number, float)

    return any(
        [is_int, is_float]
    )


def string_to_bool(arg, parser):
    if arg is not None and isinstance(arg, str):
        if arg.lower() in {'true', 't', 'yes', 'y', 'on', '1'}:

            return True

        elif arg.lower() in {'false', 'f', 'no', 'n', 'off', '0'}:

            return False

        else:
            raise parser.error(
                'Please enter a boolean-like value for this argument.'
            )
    else:
        pass


def check_same_day(last, current):
    """
    Returns True if day changed since last read.
    """
    if last != current:
        if current > last:
            return True
        else:
            raise DateCompareException

    return False


def stop_expired(current, stop, stop_time) -> bool:
    """
    Returns True is stop time is expired
    """
    time_since_stop = current["datetime"] - stop

    return time_since_stop.total_seconds() > stop_time


def increment_time_elapsed(settings, n):
    time_elapsed_restore = datetime.datetime.strptime(
        settings.get('time_elapsed', '0:00:00'), '%H:%M:%S'
    )

    time_elapsed = datetime.timedelta(
        hours=time_elapsed_restore.hour,
        minutes=time_elapsed_restore.minute,
        seconds=time_elapsed_restore.second
    ).total_seconds()

    time_elapsed += n

    return format_seconds(time_elapsed)


def compute_differences(settings, settings_prev):
    """
    Given two settings dictionary from different cycles,
    computes difference in every field and returns
    a new dictionary having identical fields but boolean value.

    True if there was a difference, False else
    """
    return {
        k: True if v != settings_prev.get(k) else False
        for k, v in settings.items()
    }
