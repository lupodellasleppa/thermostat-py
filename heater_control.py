#!/usr/bin/python3

from relay import Relay

def turn_heater_on(max_time=3600):
    '''
    Main function to turn the heater on.

    :param max_time: Is the maximum time the heater will be on,
                    after which it will turn itself off automatically.
    '''

    heater_switch = Relay(36)
    heater_switch.on()
    heater_switch.catch_sleep(max_time)
    heater_switch.clean()


if __name__ == '__main__':
    import sys

    max_time = 3600

    if len(sys.argv) > 1:
        try:
            max_time = int(sys.argv[1])
        except ValueError as e:
            content = e.args[0]
            invalid = content[content.find(':')+2:]
            raise ValueError(
                "Argument cannot be interpreted as an integer: {}".format(
                    invalid
                )
            )

    turn_heater_on(max_time)
