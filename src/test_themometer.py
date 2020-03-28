#!/usr/bin/python3

import asyncio

from thermometer import Thermometer

async def main():

    thermometer = Thermometer('192.168.1.112', 4210, 60)
    temperature = asyncio.create_task(thermometer.request_temperatures())
    print('Doing stuff...')
    temperature = await temperature

    return temperature

if __name__ == '__main__':
    print(asyncio.run(main()))
