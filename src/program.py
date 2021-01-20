#!/usr/bin/python3

import argparse
import json
import logging
import os

import util


logger_name = 'thermostat'
logger = logging.getLogger(logger_name)

class Program(object):

    def __init__(self, program_number, program_path, examples_path):

        self.program_path = program_path
        self.program_example_path = os.path.join(
            os.path.split(program_path)[0], 'example_program.json'
        )

        if not os.path.isfile(self.program_path):
            with open(self.program_example_path) as r:
                program_example = json.load(r)
            program_example = {'0': program_example}
            with open(self.program_path, 'w') as w:
                w.write(json.dumps(program_example))

        self.program = self.load_program(program_number)
        self.program_number = program_number

    def load_program(self, program_number):

        program = self.read_program()
        try:
            return program[str(program_number)]
        except ValueError as e:
            raise e

    def edit_program(self, program_number, days, hours, value):
        '''
        Writes to program.json to program thermostat

        :param day:      Weekday to modify. Can be a list or a string
        :param hour:     Hour to modify. Can be a list or a string
        '''

        # if day or hour not lists make them lists
        if not isinstance(days, list):
            days = [days]
        if not isinstance(hours, list):
            hours = [hours]

        # exception messages
        invalid_day_message = (
            'Please enter a valid day of the week'
            ' (English, case insensitive)'
        )
        invalid_hour_message = (
            "Argument 'hour' should be a number between 0 and 23"
        )

        # type checks
        try:
            program_number = str(int(program_number))
        except ValueError:
            raise ValueError("Argument 'program_number' should be an integer.")
        try:
            days = [d.lower().replace(' ', '') for day in days]
        except AttributeError:
            raise AttributeError(invalid_day_message)
        try:
            hours = [str(int(h)) for hour in hours]
        except ValueError:
            ValueError(invalid_hour_message)

        # check program number exists
        try:
            program = self.read_program()[program_number]
        except KeyError:
            raise KeyError('Could not find specified program number.')

        # edit the configuration
        for day in days:
            # d = d.lower().replace(' ', '')
            # check day
            assert d in util.days_of_week.values(), invalid_day_message
            for hour in hours:
                # check hour
                assert hour in {
                    str(el) for el in range(24)
                }, invalid_hour_message
                # insert value
                program[day][hour] = value

        self.write_program(program)

    def add_program(mode='new', program_number=None):

        assert mode in {'new', 'copy'}, "Only 'new' and 'copy' modes allowed"

        invalid_program_number_message = (
            'An number must be assigned to program_number'
            " when mode='copy' is set."
        )

        program = self.read_program()
        latest_program = int(max(
            [str(k) for k in program.keys()], key=lambda x: int(x)
        ))
        with open(self.program_example_path) as f:
            example_program = json.load(f)

        if mode == 'new':
            if program_number is None:
                program[str(latest_program + 1)] = example_program
                write_program(program)
            else:
                program[program_number] = example_program
                write_program(program)
        else:
            assert program_number is not None and isinstance(
                program_number, int
            ), invalid_program_number_message
            try:
                program[str(latest_program + 1)] = program[
                    str(program_number)
                ]
            except ValueError:
                raise ValueError(invalid_program_number_message)

            write_program(program)

    def read_program(self):

        with open(self.program_path) as f:
            program = json.load(f)

        return program

    def write_program(self, program):

        with open(self.program_path, 'w') as f:
            f.write(json.dumps(program))
            f.write("\n")


def main():

    parser = argparse.ArgumentParser(
        description=(
            'Edit thermostat program.'
        )
    )
    # does't need other params, but will be more specific if provided
    parser.add_argument(
        '-r', '--read',
        help='To check at a program without editing.',
        type=bool,
        default=False
    )
    # needs day and hour (can be lists)
    parser.add_argument(
        '-e', '--edit',
        help='Edit a program.',
        type=bool,
        default=False
    )
    # does not require params. Doesn't care about day or hour
    parser.add_argument(
        '-a', '--add',
        help='Add a new program from scratch.',
        type=bool,
        default=False
    )
    # requires program number. Doesn't care about day or hour
    parser.add_argument(
        '-c', '--copy',
        help='Create a new program copying configuration from a previous one.',
        type=bool,
        default=False
    )

    parser.add_argument(
        '-p', '--program',
        help='Choose a program number to edit.',
        type=str,
        default=None
    )

    parser.add_argument(
        '-d', '--day',
        help='Enter the days of the week you wish to edit.',
        type=str,
        nargs='+'
    )

    parser.add_argument(
        '-H', '--hour',
        help='Enter the hours you wish to edit.',
        type=str,
        nargs='+'
    )

    args = parser.parse_args

    # program_read = read_program()
    existing_programs = set(program.keys())

    if not args.add:

        if not args.read:
            assert args.program is not None, 'Please enter a program number.'
            assert args.program in existing_programs, (
                'Not a valid program number.'
            )

        if not args.copy:
            # add and copy don't care about day or hour
            if not args.day:
                args.day = list(util.days_of_week.values())
            if not args.hour:
                args.hour = list(range(24))

    elif args.add:

        assert args.program not in existing_programs, 'Program already exists.'


    if args.read:
        return _read(args.program, args.day, args.hour)




def _read(program_number, day, hour):

    res = ''

    if not program_number:
        return program_read

    program = Program(program_number)

    for day in day:
        for hour in hour:
            res += template(program_number, day, hour)


def template(program=True):
    pass







if __name__ == '__main__':

    main()
