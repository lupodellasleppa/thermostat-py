#!/usr/bin/python3

import json
import os

class LogHandler():

    def __init__(self, log_path):
        self.log_path = log_path

    def write_log(self, data):
        if (
            not os.path.isfile(self.log_path) or
            not os.stat(self.log_path).st_size
        ):
            with open(self.log_path, "w") as f:
                f.write(json.dumps([data], indent=2))
                f.write("\n")
        else:
            with open(self.log_path) as f:
                log_file = json.load(f)
            log_file.append(data)
            with open(self.log_path, "w") as f:
                f.write(json.dumps(log_file, indent=2))
                f.write("\n")
        return "Wrote log to file."

    def save_daily_entry(self, time_elapsed, last):
        data = {
            "date": last,
            "time_elapsed": time_elapsed
        }
        self.write_log(data)
