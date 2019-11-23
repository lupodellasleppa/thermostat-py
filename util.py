#!/usr/bin/python3

import datetime
import logging
import os
import time


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
        'day': current_day,
        'weekday': current_weekday,
        'hours': current_hour,
        'minutes': current_minute,
        'seconds': current_second,
        'microseconds': current_microsecond,
        'total_seconds': current_total_seconds,
        'formatted_time': str(datetime.timedelta(
            seconds=round(current_total_seconds)
        )), # TODO: use function format_seconds() below
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
            f.write(json.dumps(data, indent=2))
            f.write('\n')

    return 'Wrote log to file.'


def format_seconds(seconds):

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
