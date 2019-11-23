#!/usr/bin/python3

import argparse
import json
import os

import util


class Program(object):

    def __init__(self, program_number):

        repo_path = '/home/pi/raspb-scripts'

        self.program_path = os.path.join(repo_path, 'program.json')
        self.program_example_path = os.path.join(
            repo_path, 'example_program.json'
        )

        if not os.path.isfile(self.program_path):
            with open(self.program_example_path) as r:
                program_example = json.load(r)
            program_example = {'0': program_example}
            with open(self.program_path, 'w') as w:
                w.write(json.dumps(program_example))

        self.program = self.load_program(program_number)
        self.program_number = program_number
``
    def load_program(self, program_number):

        program = self.read_program()
        try:
            program_number = int(program_number)
        except ValueError:
            raise ValueError("Value for 'program_number' must be a number")
        try:
            return program[str(program_number)]
        except ValueError as e:
            raise e

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
            day = [d.lower().replace(' ', '') for d in day]
        except AttributeError:
            raise AttributeError(invalid_day_message)
        try:
            hour = [str(int(h)) for h in hour]
        except ValueError:
            ValueError(invalid_hour_message)

        # check program number exists
        try:
            program = self.read_program()[program_number]
        except KeyError:
            raise KeyError('Could not find specified program number.')

        # edit the configuration
        for d in day:
            d = d.lower().replace(' ', '')
            # check day
            assert d in util.days_of_week.values(), invalid_day_message
            for h in hour:
                # check hour
                assert h in {str(el) for el in range(24)}, invalid_hour_message
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
