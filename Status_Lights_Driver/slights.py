""" This package provides the interface for the system to change the status lights."""
import RPi.GPIO as GPIO
import time

import sys
import os
sys.path.append(os.path.abspath('../Hand_Classes')) # Adds higher directory to python modules path.

from enum import Enum

class pinouts(Enum):
    """The pin number for a given LED color."""
    white: 11   #GPIO 0
    yellow: 13  #GPIO 2
    blue: 15    #GPIO 3

class status_states(Enum):
    """Status states as defined by a title corresponding to a dictionary of pinout High/Lows for each color."""
    no_object: {
        pinouts.white: GPIO.LOW,
        pinouts.yellow: GPIO.HIGH,
        pinouts.blue: GPIO.LOW
    }

    object_detected: {
        pinouts.white: GPIO.LOW,
        pinouts.yellow: GPIO.LOW,
        pinouts.blue: GPIO.HIGH
    }

    object_detected_and_user_activated: {
        pinouts.white: GPIO.HIGH,
        pinouts.yellow: GPIO.LOW,
        pinouts.blue: GPIO.LOW
    }

class slights_interface():

    status_dispatcher = {}

    def __init__(self):
        #Set the GPIO pin naming convention
        GPIO.setmode(GPIO.BCM)
        #Disable warnings (not for development use)
        # GPIO.setwarnings(False)

        #Set all pinouts as GPIO Output
        for pinout in pinouts:
            GPIO.setup(pinout,GPIO.OUT)

        #Set initial status
        self.set_status(False, False)

        #Define a matching set between status states and inputs to set_status
        self.status_dispatcher = {
            #(object_detected, user_activated): display_state
            (False, False): status_states.no_object,
            (False, True): status_states.object_detected_and_user_activated,
            (True, True):  status_states.object_detected_and_user_activated,
            (True, False):  status_states.object_detected,
        }

    def set_status(self, object_detected, is_activated):
        #Correlate the state of the arm to a status light display state
        status = self.status_dispatcher[(object_detected, is_activated)]

        #Update the pins given the guidelines in the display state
        for pin in status:
            GPIO.setup(pin, status[pin])

        #Update current status
        self.current_status = status

    def get_current_status(self):
        return self.current_status

    
