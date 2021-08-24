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

import time
import subprocess

from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

#Tutorial for the display
#https://learn.adafruit.com/adafruit-pioled-128x32-mini-oled-for-raspberry-pi/usage

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
                self.lights[pinout].frequency = 1e3

        #Define a matching set between status states and inputs to set_status
        self.object_status_dispatcher = {
            True: status_states.object_detected,
            False: status_states.no_object
        }

        self.user_status_dispatcher = {
            input_types.down: status_states.user_active,
            input_types.none: status_states.user_not_active
        }

        #Initialize the display
        self.i2c = busio.I2C(SCL, SDA)
        self.disp = adafruit_ssd1306.SSD1306_I2C(128, 32, self.i2c)
        self.disp.fill(0)
        self.disp.show()
        self.width = self.disp.width
        self.height = self.disp.height
        self.image = Image.new("1", (self.width, self.height))

        # Get drawing object to draw on image.
        self.draw = ImageDraw.Draw(self.image)

        # Draw a black filled box to clear the image.
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        # self.font = ImageFont.truetype('/home/mendel/new_dev/linux_dev/monofonto.otf', 35)
        font = ImageFont.load_default()

        #Set initial status
        # self.set_status(False, False)
        self.startup_complete = False
        self.object_pulse_T0 = 0
        self.spotted_object = ""

        #Stored list of led objects if on a threaded pulse
        # self.threaded_leds = {status_states.grip_saved_id.value: [GPIO.PWM(pinouts.yellow.value, 100), False]}

    def set_status(self, object_detected, is_activated, reported_object):
        """Set the status of the lights given a combination of if an object is detected, and if the user has taken control."""
        #Correlate the state of the arm to a status light display state
        object_status = self.object_status_dispatcher[object_detected]
        user_status = self.user_status_dispatcher[is_activated]
        statuses = [object_status, user_status] #Create statuses list to iterate through, ez updating

        #Update the display with the object
        # Draw a black filled box to clear the image.
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)    
        self.draw.text((0, 0), reported_object, font=self.font, fill=255)
        self.disp.image(self.image)
        self.disp.show() 

        #Update the pins given the guidelines in the display state
        for status in statuses:
            stat = status.value
            for pin in stat:
                try:
                    self.lights[pin].write(stat[pin])
                except Exception as e:
                    if object_detected and (reported_object != self.spotted_object):
                        self.spotted_object = reported_object
                        pulse_thread = threading.Thread(target=self.pulse_vibes, args=(0.25,))
                        pulse_thread.start()
                    elif not object_detected and (reported_object != self.spotted_object):
                        self.object_pulse_T0 = 0
                        self.spotted_object = "" #the default "no object" 
                        pulse_thread = threading.Thread(target=self.pulse_vibes, args=(0.05,))
                        pulse_thread.start()

    def pulse_vibes(self, vibe_time):
        if vibe_time == 0.05:
            self.vibe_status = "Short pulse"
        elif vibe_time == 0.25:
            self.vibe_status = "Long pulse"
        self.lights[pinouts.vibrate].duty_cycle = 1
        time.sleep(vibe_time)
        self.lights[pinouts.vibrate].duty_cycle = 0
        self.vibe_status = "N/A"

    def pulse_thread(self):
        pass

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
        # while not self.startup_complete:
        #     try:
        #         for dc in range(0, 10, 1):
        #             self.lights[pinouts.vibrate].duty_cycle = float(dc/10)
        #             time.sleep(0.1)
        #         for dc in range(10, 0, -1):
        #             self.lights[pinouts.vibrate].duty_cycle = float(dc/10)
        #             time.sleep(0.1)
        #         # self.lights[pinouts.vibrate].enable()
        #     except Exception as e:
        #         print(str(e))
        pulse_time = 0.1
        self.pulse_vibes(pulse_time)
        time.sleep(pulse_time)
        self.pulse_vibes(pulse_time)
        time.sleep(pulse_time)
        self.pulse_vibes(pulse_time)
        time.sleep(pulse_time)
        self.lights[pinouts.vibrate].duty_cycle = 0

    def safe_shutdown(self):
        """Funky shutdown sequence to indicate to the user the arm is shutting down."""
        pulse_time = 0.1
        self.pulse_vibes(pulse_time)
        time.sleep(pulse_time)
        self.pulse_vibes(pulse_time)
        time.sleep(pulse_time)
        self.pulse_vibes(pulse_time)
        time.sleep(pulse_time)
        #Pause for effect
        #Turn them all off
        for pinout in pinouts:
            self.lights[pinout].close()

        print("[STATUS] Successfully killed GPIO.")

    
