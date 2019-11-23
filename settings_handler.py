#!/usr/bin/python3

import argparse
import json
import logging
import os

logger_name = 'thermostat'
logging.basicConfig(
    format='{levelname:<8} {asctime} - {message}',
    style='{'
)
logger = logging.getLogger(logger_name)
logger.setLevel(logging.DEBUG)


def create_parser():

    parser = argparse.ArgumentParser(
        description=(
            'Edits the settings.json file ruling the heater behavior.'
        )
    )

    parser.add_argument(
        "-m", "--manual",
        help="Set manual to ON. Turns ON heater."
    )

    parser.add_argument(
        "-a", "--auto",
        help="Set auto to ON. Turns ON heater according to program."
    )

    parser.add_argument(
        "-p", "--program",
        help="Insert the program number you wish to load.",
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

    args.manual = string_to_bool(args.manual)
    args.auto = string_to_bool(args.auto)

    logger.debug(
        f'manual: {args.manual}; auto: {args.auto}; program: {args.program};'
    )

    if args.manual is None and args.auto is None and args.program is None:
        raise parser.error(
            "Please enter at least one argument."
            " Type '--help' for more information."
        )

    return args


def main(time_elapsed=None):

    args = create_parser()

    settings_path = 'settings.json'
    settings_file = load_settings(settings_path)
    settings_changes = {
        "program": (
            args.program if args.program is not None
            else settings_file['program']
        ),
        "auto": (
            args.auto if args.auto is not None
            else settings_file['auto']
        ),
        "manual": (
            args.manual if args.manual is not None
            else settings_file['manual']
        )
    }

    handler(settings_changes=settings_changes)


def load_settings(settings_path):

    if not os.path.isfile(settings_path) or not os.stat(settings_path).st_size:
        settings_file = {
            "program": 0,
            "auto": False,
            "manual": False
        }
        with open(settings_path, 'w') as f:
            f.write(json.dumps(settings_file, indent=2))
        logger.debug('Created settings.json file.')

    with open(settings_path) as f:
        settings_file = json.load(f)

    return settings_file


def update_settings(settings_changes, settings_file, settings_path):

    if settings_changes != settings_file:
        settings_changes = json.dumps(settings_changes, indent=2)
        logger.debug('\n' + settings_changes)
        logger.debug("Settings changed!")
        with open(settings_path, 'w') as f:
            f.write(settings_changes)
            f.write('\n')
    else:
        logger.debug("Settings not changed.")

    return load_settings(settings_path)


def handler(time_elapsed=None, settings_changes={}):

    settings_path = 'settings.json'
    settings_file = load_settings(settings_path)

    if time_elapsed is not None:
        if settings_changes is not None:
            settings_changes.update({'time_elapsed': time_elapsed})
        else:
            settings_changes = {'time_elapsed': time_elapsed}

    settings_changes.update(
        {k:v for k, v in settings_file.items() if k not in settings_changes}
    )

    return update_settings(settings_changes, settings_file, settings_path)


if __name__ == '__main__':
    main()
