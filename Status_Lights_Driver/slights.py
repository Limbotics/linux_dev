""" This package provides the interface for the system to change the status lights."""
import RPi.GPIO as GPIO
import time

import sys
import os
sys.path.append(os.path.abspath('../Hand_Classes')) # Adds higher directory to python modules path.

from Hand_Classes import hand_interface
grips = hand_interface.grips

from enum import Enum

class pinouts(Enum):
    """The pin number for a given LED color. BCM Coordinate system"""
    white  = 17   #GPIO 0
    yellow = 27  #GPIO 2
    blue   = 22    #GPIO 3

class status_states(Enum):
    """Status states as defined by a title corresponding to a dictionary of pinout High/Lows for each color."""
    no_object = {
        pinouts.white: GPIO.LOW,
        pinouts.yellow: GPIO.HIGH,
        pinouts.blue: GPIO.LOW
    }

    object_detected = {
        pinouts.white: GPIO.LOW,
        pinouts.yellow: GPIO.LOW,
        pinouts.blue: GPIO.HIGH
    }

    object_detected_and_user_activated = {
        pinouts.white: GPIO.HIGH,
        pinouts.yellow: GPIO.LOW,
        pinouts.blue: GPIO.LOW
    }

class slights_interface():
    """
    Status Lights interfacing for startup, shutdown, and different operational modes.
      
    Attributes:
        status_dispatcher (dict): Correlates a tuple of (object_detected, user_activated) to a state of the status lights.
        current_status (dict): The current state of all the lights, an enum in status_states. 
        
    """

    def __init__(self):
        #Set the GPIO pin naming convention
        GPIO.setmode(GPIO.BCM)

        #Disable warnings (not for development use)
        # GPIO.setwarnings(False)

        #Set all pinouts as GPIO Output
        for pinout in pinouts:
            GPIO.setup(pinout.value,GPIO.OUT)

        #Define a matching set between status states and inputs to set_status
        self.status_dispatcher = {
            #(object_detected, user_activated): display_state
            (False, False): status_states.no_object.value,
            (False, True): status_states.object_detected_and_user_activated.value, #TODO: New status for this?
            (True, True):  status_states.object_detected_and_user_activated.value,
            (True, False):  status_states.object_detected.value,
        }

        #Run the startup sequence
        self.startup_sequence()

        #Set initial status
        self.set_status(False, False)

    def set_status(self, object_detected, is_activated):
        """Set the status of the lights given a combination of if an object is detected, and if the user has taken control."""
        #Correlate the state of the arm to a status light display state
        status = self.status_dispatcher[(object_detected, is_activated)]

        #Update the pins given the guidelines in the display state
        for pin in status:
            GPIO.output(pin.value, status[pin])

        #Update current status
        self.current_status = status

        #print("Updated LED status to " + str(self.current_status))

    def get_current_status(self):
        return self.current_status

    def startup_sequence(self):
        """Funky startup sequence to indicate to the user the arm is starting up."""
        for pinout in pinouts:
            GPIO.output(pinout.value,GPIO.HIGH)
            time.sleep(0.1)
        for pinout in pinouts:
            GPIO.output(pinout.value,GPIO.LOW)
            time.sleep(0.1)

    def safe_shutdown(self):
        """Funky shutdown sequence to indicate to the user the arm is shutting down."""
        #Set them all to off
        for pinout in pinouts:
            GPIO.output(pinout.value,GPIO.LOW)
        #Set them all to high, sequentially
        for pinout in pinouts:
            GPIO.output(pinout.value,GPIO.HIGH)
            time.sleep(0.1)
        #Pause for effect
        time.sleep(0.25)
        #Turn them all off
        for pinout in pinouts:
            GPIO.output(pinout.value,GPIO.LOW)

    
