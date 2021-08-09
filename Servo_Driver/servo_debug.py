from adafruit_servokit import ServoKit
#https://learn.adafruit.com/adafruit-16-channel-pwm-servo-hat-for-raspberry-pi/using-the-python-library#controlling-servos-3013804-22
#LINUX FIX:
# #https://gitmemory.com/issue/adafruit/Adafruit_Blinka/328/672356503
from enum import Enum
import time

import sys
import os

#Import interface enums from hand_interface
class handServoControl:
    """
    Low-level servo control in terms of specific servo channels and angle commands.
      
    Attributes:
        angles (dict): The current angle that each finger (servo) is set to.
        kit (ServoKit): The Servokit object.
    """
    def __init__(self):

        #this class is the lookup table servo control because the functions kind of do everything already 
        #16 channel piHat
        self.kit = ServoKit(channels=16)

    def moveFinger(self, finger, angle):
        """Command a given finger to a certain angle.
        
        Parameters:
            finger (int): One of the hand_interfaces.fingers values to dictate which channel to command a servo.

            angle (int):  The angle to which to command the given servo to.

        """
        self.kit.servo[finger].angle = angle
        time.sleep(0.1)

try:
    servos = handServoControl()
    while(True):
        print("What finger would you like to command?")
        print("\tThumb: 0")
        print("\tPointer: 1")
        print("\tMiddle: 2")
        print("\tRing/Pinky: 3")
        finger = int(input()) #This is the finger servo channel
        if finger == 69:
            break
        print("What angle do you want to command it to?")
        angle = int(input("Put in desired angle BOII"))
        servos.moveFinger(finger, angle)

except KeyboardInterrupt:
    print("Program exit command detected!")
    pass
