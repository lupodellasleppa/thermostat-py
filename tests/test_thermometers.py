import logging
import pytest

from thermostat_py.managers import ThermometerManager
from thermostat_py.thermometers import ThermometerWired, ThermometerWireless


logger = logging.getLogger("test_thermometers")


@pytest.fixture
def thermometers_manager():
    return ThermometerManager


def test_thermometers_manager(thermometers_manager):
    tm = thermometers_manager()

    thermometer_wired_values = {
        "name": "wired",
        "description": "a wired sensor",
        "read_period": 30,
        "thermometer_type": "wired",
    }

    thermometer_wireless_values = {
        "name": "wireless",
        "description": "a wireless sensor",
        "host": "127.0.0.1",
        "port": 11011,
        "read_period": 30,
        "send_period": 60,
        "thermometer_type": "wired",
        "timeout": 1
    }

    tm.add("wired", thermometer_wired_values)
    tm.add("wireless", thermometer_wireless_values)

    for name, thermometer in tm.wired.items():
        logger.info("Thermometer wired: {}".format(thermometer))
        assert isinstance(thermometer, ThermometerWired)

    for name, thermometer in tm.wireless.items():
        logger.info("Thermometer wireless: {}".format(thermometer))
        assert isinstance(thermometer, ThermometerWireless)
