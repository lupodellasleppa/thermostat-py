#!/usr/bin/python3

import argparse
import json
import logging
import os
import util


logger_name = 'thermostat'
logger = logging.getLogger(logger_name)


def create_parser():
    '''
    Defines script's arguments.
    '''

    parser = argparse.ArgumentParser(
        description=(
            'Edits the settings.json file ruling the heater behavior.'
        )
    )

    parser.add_argument(
        '-a', '--auto',
        help='Set auto to ON. Turns ON heater according to program.'
    )

    parser.add_argument(
        '-l', '--loglevel',
        help='Defines the log level for logger in scripts.',
        type=str
    )

    parser.add_argument(
        '-m', '--manual',
        help='Set manual to ON. Turns ON heater.'
    )

    parser.add_argument(
        '-p', '--program',
        help='Insert the program number you wish to load.',
        type=int
    )

    parser.add_argument(
        '-t', '--temperature',
        help='Insert the desired temperature when in manual mode.',
        type=int
    )

    args = parser.parse_args()
    logger.debug(
        f'manual: {args.manual}; auto: {args.auto}; program: {args.program};'
    )

    def string_to_bool(arg):

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

    def int_to_string(arg):

        if arg is not None:
            if isinstance(arg, int):
                return str(arg)
            else:
                raise parser.error(
                    'Please enter an integer.'
                )

    args.manual = string_to_bool(args.manual)
    args.auto = string_to_bool(args.auto)

    logger.debug(
        f'manual: {args.manual}; auto: {args.auto}; program: {args.program};'
    )

    if (
        args.auto is None and
        args.loglevel is None and
        args.manual is None and
        args.program is None and
        args.temperature is None
    ):
        raise parser.error(
            'Please enter at least one argument.'
            " Type '--help' for more information."
        )

    return args


def main(time_elapsed=None):
    '''
    Function called when script is called directly.
    Takes argument from argparse defined in create_parser function.
    '''

    args = create_parser()

    settings_path = 'settings.json'
    settings_file = load_settings(settings_path)
    settings_changes = {
        'auto': (
            args.auto if args.auto is not None
            else settings_file['auto']
        ),
        'loglevel': (
            args.loglevel if args.loglevel is not None
            else settings_file['loglevel']
        ),
        'manual': (
            args.manual if args.manual is not None
            else settings_file['manual']
        ),
        'program': (
            args.program if args.program is not None
            else settings_file['program']
        ),
        'temperature': (
            args.temperature if args.temperature is not None
            else settings_file['temperature']
        )
    }

    return handler(
        settings_path=settings_path,
        settings_changes=settings_changes
    )


def load_settings(settings_path):
    '''
    Return setting in 'setting.json' file in a python dictionary.
    '''

    if not os.path.isfile(settings_path) or not os.stat(settings_path).st_size:
        settings_file = {
            'program': '0',
            'auto': False,
            'last_day_on': util.get_now()['formatted_date'],
            'loglevel': 'INFO',
            'manual': False,
            'time_elapsed': '0:00:00',
            'time_to_wait': 1
        }
        with open(settings_path, 'w') as f:
            f.write(json.dumps(settings_file, indent=2))
        logger.debug('Created settings.json file.')

    with open(settings_path) as f:
        settings_file = json.load(f)

    return settings_file


def update_settings(settings_changes, settings_file, settings_path):
    '''
    Write setting_changes to 'setting.json' file.
    Returns contents of the file in a python dictionary.
    '''

    if settings_changes != settings_file:
        settings_changes = json.dumps(settings_changes, indent=2)
        logger.debug('\n' + settings_changes)
        logger.debug('Settings changed!')
        with open(settings_path, 'w') as f:
            f.write(settings_changes)
            f.write('\n')
    else:
        logger.debug('Settings not changed.')

    return load_settings(settings_path)


def handler(settings_path, settings_changes={}):
    '''
    Sends updates to update_settings function.
    Returns contents of 'settings.json' after updates in a python dictionary.
    '''

    settings_path = 'settings.json'
    settings_file = load_settings(settings_path)

    logger.debug('Settings file read: {}'.format(settings_file))
    logger.debug('Settings before update: {}'.format(settings_changes))

    settings_changes.update(
        {k:v for k, v in settings_file.items() if k not in settings_changes}
    )
    logger.debug('Settings after update: {}'.format(settings_changes))

    return update_settings(settings_changes, settings_file, settings_path)


if __name__ == '__main__':
    main()
