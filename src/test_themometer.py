#!/usr/bin/python3

import asyncio
import time

from exceptions import ThermometerTimeout
from thermometer import ThermometerLocal

async def main():

    thermometer = ThermometerLocal('192.168.1.112', 4210, 0.5)
    temperature = None
    print('Doing stuff...')
    retries = 0
    while not temperature and retries < 5:
        temperature_task = asyncio.create_task(thermometer.request_temperatures())
        try:
            temperature = await temperature_task
        except ThermometerTimeout:
            pass
        retries += 1

    return temperature, retries

if __name__ == '__main__':
    start = time.monotonic()
    print(asyncio.run(main()))
    end = time.monotonic()
    print('Elapsed time: {}'.format(end - start))
