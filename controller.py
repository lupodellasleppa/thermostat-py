#!/usr/bin/python3

import logging
import threading

import relay


logger = logging.getLogger('thermostat')

class Controller(threading.Thread):

    
