""" This package provides the interface for the system to change the status lights."""
from periphery import GPIO
from periphery import PWM
import time

import sys
import os
import threading
sys.path.append(os.path.abspath('../Hand_Classes')) # Adds higher directory to python modules path.

from Hand_Classes import hand_interface
grips = hand_interface.grips
input_types = hand_interface.input_types

from enum import Enum

class pinouts(Enum):
    #Use https://coral.ai/docs/dev-board-mini/gpio/#header-pinout to find path, chip, and line for each pin
    #Note: Pins 8, 10, 29, 31, and 37 should not be used to drive resistive loads directly, due to weak drive strength.
    """The device path, chip, and line for each pin"""

    green  =  { #GPIO0, pin 16
        "path": "/dev/gpiochip2",
        "line": 9
    }
    blue   = { #GPIO1, pin 18
        "path": "/dev/gpiochip4",
        "line": 10
    }   
    yellow = { #GPIO7, pin 22
        "path": "/dev/gpiochip4",
        "line": 12
    }
    vibrate = {
        "chip": 0,
        "line": 0
    }

class status_states(Enum):
    """Status states as defined by a title corresponding to a dictionary of pinout High/Lows for each color."""
    #Blue light = object detection indicator. Blue on means object seen. Blue off means no object seen.
    no_object = {
        pinouts.vibrate: False
    }

    object_detected = {
        pinouts.vibrate: True
    }

    #Green light = user input indicator. Green on means user input detected. Green off means no user input detected. 
    user_active = {
        pinouts.green: True
    }

    user_not_active = {
        pinouts.green: False
    }

    #Standby state
    standby = {
        pinouts.yellow: True
    }

    #Saved grip state
    grip_saved = {
        pinouts.yellow: True
    }

    grip_saved_id = 'status_save'

class slights_interface():
    lights = {}
    """
    Status Lights interfacing for startup, shutdown, and different operational modes.
      
    Attributes:
        status_dispatcher (dict): Correlates a tuple of (object_detected, user_activated) to a state of the status lights.
        current_status (dict): The current state of all the lights, an enum in status_states. 
        lights (dict): The dictionary of pinouts to their corresponding GPIO interface objects.
        
    """

    def __init__(self):
        #Set the GPIO pin naming convention
        #GPIO.setmode(GPIO.BCM)

        #Disable warnings (not for development use)
        # GPIO.setwarnings(False)

        #Set all pinouts as GPIO Output
        for pinout in pinouts:
            try:
                self.lights[pinout] = GPIO(pinout.value["path"], pinout.value["line"], "out")
            except Exception as e:
                self.lights[pinout] = PWM(pinout.value["chip"], pinout.value["line"])

        #Define a matching set between status states and inputs to set_status
        self.object_status_dispatcher = {
            True: status_states.object_detected,
            False: status_states.no_object
        }

        self.user_status_dispatcher = {
            input_types.down: status_states.user_active,
            input_types.none: status_states.user_not_active
        }

        #Run the startup sequence
        # self.startup_sequence()

        #Set initial status
        # self.set_status(False, False)
        self.startup_complete = False

        #Stored list of led objects if on a threaded pulse
        # self.threaded_leds = {status_states.grip_saved_id.value: [GPIO.PWM(pinouts.yellow.value, 100), False]}

    def set_status(self, object_detected, is_activated):
        """Set the status of the lights given a combination of if an object is detected, and if the user has taken control."""
        #Correlate the state of the arm to a status light display state
        object_status = self.object_status_dispatcher[object_detected]
        user_status = self.user_status_dispatcher[is_activated]
        statuses = [object_status, user_status] #Create statuses list to iterate through, ez updating

        #Update the pins given the guidelines in the display state
        for status in statuses:
            stat = status.value
            for pin in stat:
                try:
                    self.lights[pin].write(stat[pin])
                except Exception as e:
                    self.lights[pin].frequency = 1e3
                    if object_detected:
                        self.lights[pin].duty_cycle = 1
                    else:
                        self.lights[pin].duty_cycle = 0
                #GPIO.output(pin.value, stat[pin])

    def pulse_thread(self):
        pass
        # #Get which LED we're working with from the thread key
        # thread_key = status_states.grip_saved_id.value
        # led = self.threaded_leds[thread_key][0]
        # led.start(0)
        # self.threaded_leds[thread_key][1] = True #Set the loop to run 
        # print("[DEBUG] Starting LED pulse")
        # while self.threaded_leds[thread_key][1]:
        #     #Turn up brightness
        #     for dc in range(0, 50, 5):
        #         led.ChangeDutyCycle(dc)
        #         time.sleep(0.1)
        #     #Turn down brightness
        #     for dc in range(50, -1, -5):
        #         led.ChangeDutyCycle(dc)
        #         time.sleep(0.1)
        # #Reset the duty cycle
        # led.ChangeDutyCycle(100)

    def startup_sequence(self):
        """Funky startup sequence to indicate to the user the arm is starting up."""
        for pinout in pinouts:
            self.lights[pinout].write(True)
            time.sleep(0.1)
        for pinout in pinouts:
            self.lights[pinout].write(False)
            time.sleep(0.1)

    def startup_wait(self):
        #run indefinitely until flag is thrown that the rest of the system is ready
        self.lights[pinouts.vibrate].frequency = 1e3
        # Set duty cycle to 75%
        self.lights[pinouts.vibrate].duty_cycle = 0
        self.lights[pinouts.vibrate].enable()
        duty = 0
        delta = 0.01
        while not self.startup_complete:
            try:
                duty = duty + delta
                if duty > 1:
                    delta = -0.01
                    duty = duty + delta
                elif duty < 0:
                    delta = 0.01
                    duty = duty + delta
                self.lights[pinouts.vibrate].duty_cycle = duty
                # self.lights[pinouts.vibrate].enable()
            except Exception as e:
                print(str(e))
            time.sleep(0.1)
        self.lights[pinouts.vibrate].duty_cycle = 0

    def safe_shutdown(self):
        """Funky shutdown sequence to indicate to the user the arm is shutting down."""
        #Set all pulse LEDs to end threads
        #self.threaded_leds[status_states.grip_saved_id.value][1] = False
        #Set them all to off
        for pinout in pinouts:
            self.lights[pinout].write(False)
        #Set them all to high, sequentially
        for pinout in pinouts:
            self.lights[pinout].write(True)
            time.sleep(0.1)
        #Pause for effect
        time.sleep(0.25)
        #Turn them all off
        for pinout in pinouts:
            self.lights[pinout].write(False)
            self.lights[pinout].close()

    
