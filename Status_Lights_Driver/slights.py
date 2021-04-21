""" This package provides the interface for the system to change the status lights."""
import RPi.GPIO as GPIO
import time

import sys
import os
import threading
sys.path.append(os.path.abspath('../Hand_Classes')) # Adds higher directory to python modules path.

from Hand_Classes import hand_interface
grips = hand_interface.grips

from enum import Enum

class pinouts(Enum):
    """The pin number for a given LED color. BCM Coordinate system"""
    green  = 17  
    blue   = 22    
    yellow = 27  

class status_states(Enum):
    """Status states as defined by a title corresponding to a dictionary of pinout High/Lows for each color."""
    #Blue light = object detection indicator. Blue on means object seen. Blue off means no object seen.
    no_object = {
        pinouts.blue: GPIO.LOW
    }

    object_detected = {
        pinouts.blue: GPIO.HIGH,
    }

    #Green light = user input indicator. Green on means user input detected. Green off means no user input detected. 
    user_active = {
        pinouts.green: GPIO.HIGH
    }

    user_not_active = {
        pinouts.green: GPIO.LOW
    }

    #Standby state
    standby = {
        pinouts.yellow: GPIO.HIGH
    }

    #Saved grip state
    grip_saved = {
        pinouts.yellow: GPIO.HIGH
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
        self.object_status_dispatcher = {
            True: status_states.object_detected,
            False: status_states.no_object
        }

        self.user_status_dispatcher = {
            True: status_states.user_active,
            False: status_states.user_not_active
        }

        #Run the startup sequence
        # self.startup_sequence()

        #Set initial status
        self.set_status(False, False)
        self.startup_complete = False

        #Stored list of led objects if on a threaded pulse
        self.threaded_leds = {status_states.grip_saved}: [GPIO.PWM(pinouts.yellow.value, 500), False]}

    def set_status(self, object_detected, is_activated, saved_state):
        """Set the status of the lights given a combination of if an object is detected, and if the user has taken control."""
        #Correlate the state of the arm to a status light display state
        object_status = self.object_status_dispatcher[object_detected]
        user_status = self.user_status_dispatcher[is_activated]
        statuses = [object_status, user_status] #Create statuses list to iterate through, ez updating

        #Lastly, do the saved state led
        if (not saved_state):
            if self.threaded_leds[status_states.grip_saved][1]:
                self.threaded_leds[status_states.grip_saved][1] = False
            statuses.append(status_states.standby)
        else:
            #Start the pulse thread for the amber light
            led_pulse_thread = threading.Thread(target=self.pulse_thread, args=(status_states.grip_saved))
            led_pulse_thread.start()

        #Update the pins given the guidelines in the display state
        for status in statuses:
            for pin in status:
                GPIO.output(pin.value, status[pin])

    def pulse_thread(self, thread_key):
        led = self.threaded_leds[thread_key][0]
        while self.threaded_leds[thread_key][1]:
            for dc in range(0, 101, 5):
                led.ChangeDutyCycle(dc)
                time.sleep(0.1)
            for dc in range(100, -1, -5):
                led.ChangeDutyCycle(dc)
                time.sleep(0.1)

    def startup_sequence(self):
        """Funky startup sequence to indicate to the user the arm is starting up."""
        for pinout in pinouts:
            GPIO.output(pinout.value,GPIO.HIGH)
            time.sleep(0.1)
        for pinout in pinouts:
            GPIO.output(pinout.value,GPIO.LOW)
            time.sleep(0.1)

    def startup_wait(self):
        #run indefinitely until flag is thrown that the rest of the system is ready
        while not self.startup_complete:
            for pinout in pinouts:
                GPIO.output(pinout.value,GPIO.HIGH)
                time.sleep(0.2)
            for pinout in pinouts:
                GPIO.output(pinout.value,GPIO.LOW)
                time.sleep(0.2)

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

    
