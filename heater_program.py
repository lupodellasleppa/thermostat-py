#!/usr/bin/python3

import json
import os


class Program(object):

    def __init__(self, program_number):

        self.days_of_week = {
            0: "monday",
            1: "tuesday",
            2: "wednesday",
            3: "thursday",
            4: "friday",
            5: "saturday",
            6: "sunday"
        }

        repo_path = '/home/pi/raspb-scripts/'

        self.program_path = os.path.join(repo_path, 'program.json')
        self.program_example_path = os.path.join(
            repo_path, 'example_program.json'
        )

        if not os.path.isfile(self.program_path):
            with open(self.program_example_path) as r:
                program_example = json.load(r)
            program_example = {0: program_example}

        self.program = self.load_program(program_number)

    def load_program(self, program_number):

        program = self.read_program()

        return program['program_number']

    def edit_program(self, program_number, day, hour, value):
        '''
        Writes to program.json to program thermostat

        :param day:      Weekday to modify. Can be a list or a string
        :param hour:     Hour to modify. Can be a list or a string
        '''

        # if day or hour not lists make them lists
        if not isinstance(day, list):
            day = [day]
        if not isinstance(hour, list):
            hour = [hour]

        # exception messages
        invalid_day_message = (
            "Please enter a valid day of the week"
            " (English, case insensitive)"
        )
        invalid_hour_message = "Please enter an integer between 0 and 23"

        # type checks
        assert isinstance(program_number, int), (
            "program_number should be an integer."
        )
        try:
            day = [d.lower().replace(' ', '') for d in day]
        except AttributeError:
            raise AttributeError(invalid_day_message)
        try:
            hour = [int(h) for h in hour]
        except ValueError:
            ValueError(invalid_hour_message)

        # check program number exists
        try:
            program = self.read_program()[program_number]
        except KeyError:
            raise KeyError("Could not find specified program number.")

        # edit the configuration
        for d.lower().replace(' ', '') in day:
            # check day
            assert d in self.days_of_week.values(), invalid_day_message
            for h in hour:
                # check hour
                assert h in set(range(24)), invalid_hour_message
                # insert value
                program[day][hour] = value

        self.write_program(program)

    def add_program(mode='new', program_to_copy=None):

        assert mode in {'new', 'copy'}, "Only 'new' and 'copy' modes allowed"

        program = read_program()
        latest_program = max(program)
        with open(self.program_example_path) as f:
            example_program = json.load(f)

        if mode == 'new':
            program[latest_program + 1] = example_program
            write_program(program)
        else:
            assert program_to_copy is not None, (
                "An integer must be assigned to program_to_copy"
                " when mode='copy' is set."
            )
            program[latest_program + 1] = program[
                program_to_copy
            ]
            write_program(program)


    def read_program(self):

        with open(self.program_path) as f:
            program = json.load(f)

        return program

    def write_program(self, program):

        with open(self.program_path, 'w') as f:
            f.write(json.dumps(program))