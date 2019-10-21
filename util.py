#!/usr/bin/python3

import datetime


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

    current_time = datetime.datetime.now()
    current_day = util.days_of_week[current_time.weekday()]
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
