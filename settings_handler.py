#!/usr/bin/python3

import argparse
import json
import logging

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

    def str2bool(arg):

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

    args.manual = str2bool(args.manual)
    args.auto = str2bool(args.auto)

    logger.debug(
        f'manual: {args.manual}; auto: {args.auto}; program: {args.program};'
    )

    if args.manual is None and args.auto is None and args.program is None:
        raise parser.error(
            "Please enter at least one argument."
            " Type '--help' for more information."
        )

    return args


def main():

    args = create_parser()

    with open('settings.json') as f:
        settings_file = json.load(f)

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

    logger.debug(settings_changes)

    if settings_changes != settings_file:
        settings_changes = json.dumps(settings_changes, indent=2)
        logger.debug('\n' + settings_changes)
        logger.debug("Settings changed!")
        with open('settings.json', 'w') as f:
            f.write(settings_changes)
            f.write('\n')
    else:
        logger.debug("Settings not changed.")


if __name__ == '__main__':
    main()
