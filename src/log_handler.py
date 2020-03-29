#!/usr/bin/python3

import os

class LogHandler():

    def __init__(self):

        pass

    def write_log(self, log_path, data):

        if (
            not os.path.isfile(log_path) or
            not os.stat(log_path).st_size
        ):
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

    def save_daily_entry(
        self, time_elapsed, last_recorded_day, current_day, daily_log_path
    ):

        data = {
            'date': current_day,
            'time_elapsed': time_elapsed
        }

        self.write_log(daily_log_path, data)

        # if (
        #     heater_poll.last_current is not None and
        #     heater_poll.last_current['day'] != current['day']
        # ):
        #     {
        #         'date': self.settings['log']['last_day_on'],
        #         'time_elapsed': util.format_seconds(self.time_elapsed)
        #     }
