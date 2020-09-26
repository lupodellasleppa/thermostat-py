#!/usr/bin/python3

import json
import socket
import time


thermometer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
thermometer.settimeout(1)
thermometer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
UDP_port = 4210
UDP_IP = '192.168.1.112'

def get_room_temp():

    thermometer.sendto(b'temps_req', (UDP_IP, UDP_port))
    time.sleep(1)
    try:
        temperature = json.loads(
                       thermometer.recv(4096).decode()
                   )['celsius']
        return temperature
    except socket.timeout:
        print('Did not receive response from thermometer, retrying...')
        get_room_temp()

if __name__ == "__main__":
    print(get_room_temp())

