#!/usr/bin/python3

import asyncio
import time

from exceptions import ThermometerTimeout
from thermometer import ThermometerLocal

async def main(retries=0):
    thermometer = ThermometerLocal('192.168.1.112', 4210, 1)
    temperature = None
    print('Doing stuff...')
    retries = 0
    # while not temperature and retries < 5:
    while not temperature:
        temperature_task = asyncio.create_task(thermometer.request_temperatures())
        print(retries)
        try:
            temperature = await temperature_task
        except ThermometerTimeout:
            retries += 1
    return temperature, retries

if __name__ == '__main__':
    g_start = time.monotonic()
    p_start = time.perf_counter()
    for i in range(3):
        start = time.monotonic()
        loop = asyncio.get_event_loop()
        a = loop.run_until_complete(main())
        print(a)
        # print(asyncio.run(main()))
        end = time.monotonic()
        print('Elapsed time: {}'.format(end - start))
        time.sleep(1)
    print("monotonic: {}".format(time.monotonic() - g_start))
    print("perf_counter: {}".format(time.perf_counter() - p_start))
