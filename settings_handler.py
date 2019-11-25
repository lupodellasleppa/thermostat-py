#!/usr/bin/python3

import argparse
import json
import logging
import os
import sys

import util


'''
Settings are made like this:

{
  "mode": {
    "auto": bool,
    "program": int,
    "manual": bool,
    "desired_temp": float
  },
  "temperatures": {
    "room": float
  },
  "log": {
    "loglevel": str,
    "global_log": str,
    "session_log": str,
    "last_day_on": "YYYY-mm-dd",
    "time_elapsed": "H:MM:SS"
  },
  "configs": {
    "UDP_IP": str,
    "UDP_port": int
  }
  "poll_intervals": {
    "settings": int,
    "temperature": int
  }
}

OLD:
{
  "auto": true,
  "loglevel": "debug",
  "logpath": "/home/pi/raspb-scripts/log.json"
  "manual": true,
  "program": 0,
  "temperature": 0,
  "last_day_on": "2019-11-23",
  "time_elapsed": "2:45:13",
  "time_to_wait": 1
}

'''


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
        type=float
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
    # define all fields that can be changed using this module
    settings_changes = {
        'mode': {
            'auto': (
                args.auto if args.auto is not None
                else settings_file['mode']['auto']
            ),
            'program': (
                args.program if args.program is not None
                else settings_file['mode']['program']
            ),
            'manual': (
                args.manual if args.manual is not None
                else settings_file['mode']['manual']
            ),
            'desired_temp': (
                args.temperature if args.temperature is not None
                else settings_file['mode']['temperature']
            )
        },
        'log': {
            'loglevel': (
                args.loglevel if args.loglevel is not None
                else settings_file['loglevel']
            )
        }
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
        logger.info('{} not found, creating.'.format(settings_path))
        with open(os.path.join(sys.path[0], 'example_settings.json')) as f:
            settings_file = json.load(f)
        with open(settings_path, 'w') as f:
            f.write(json.dumps(settings_file, indent=2))
        logger.debug('Created new settings.json file from example.')

    with open(settings_path) as f:
        settings_file = json.load(f)

    return settings_file


def update_settings(settings_changes, settings_file, settings_path):
    '''
    Write settings_changes to 'setting.json' file.
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

    settings_file = load_settings(settings_path)

    logger.debug('Settings file read: {}'.format(settings_file))
    logger.debug('Settings before update: {}'.format(settings_changes))

    # nested dict update of settings_changes
    settings_changes = {
        k:( # take outer from settings_file if not in settings_changes
            {kk:v for kk, v in settings_file[k].items()}
            if k not in settings_changes
            else { # if exists in both go deeper
                kk:( # if key not in settings_changes take v from settings_file
                    v if kk not in settings_changes[k]
                    else settings_changes[k][kk] # from settings_changes else
                ) for kk, v in settings_file[k].items()
            }
        ) for k in settings_file
    }

    logger.debug('Settings after update: {}'.format(settings_changes))

    return update_settings(settings_changes, settings_file, settings_path)


if __name__ == '__main__':
    main()
