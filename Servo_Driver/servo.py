from adafruit_servokit import ServoKit
#https://learn.adafruit.com/adafruit-16-channel-pwm-servo-hat-for-raspberry-pi/using-the-python-library#controlling-servos-3013804-22
#LINUX FIX:
# #https://gitmemory.com/issue/adafruit/Adafruit_Blinka/328/672356503
# https://www.digi.com/support/forum/19251/linux-cme9210-pca9554-i2c Fix for I2C lockup
from enum import Enum
import time

import sys
import os
sys.path.append(os.path.abspath('../Hand_Classes'))

#Import interface enums from hand_interface
from Hand_Classes import hand_interface
fingers = hand_interface.fingers
grip_names = hand_interface.grip_names
grips = hand_interface.grips

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
        self.kit = ServoKit(channels=16, )

        #Initialize stored angles
        self.angles = {
            fingers.thumb: 0,
            fingers.index: 0,
            fingers.middle: 0,
            fingers.ring: 0
            #fingers.pinky: 0
        }

    def moveFinger(self, finger, angle):
        """Command a given finger to a certain angle.
        
        Parameters:
            finger (int): One of the hand_interfaces.fingers values to dictate which channel to command a servo.

            angle (int):  The angle to which to command the given servo to.

        """
        self.kit.servo[finger].angle = angle
        self.angles[finger] = angle

#https://www.w3schools.com/python/python_inheritance.asp

#this child class is the look up table and needs the most real world tuning
class handLUTControl(handServoControl):
    """
    High-level servo control in terms of hand manipulation.
      
    Attributes:
        dispatch (dict): Correlates different grips to their respective servo angle definitions.
        grip_config (string): The current hand_interfaces.grips (values) parameter the system is set to.
        
    """
    
    def __init__(self, grip_config=hand_interface.grip_angles.lateral_power.value):
        super().__init__()
        self.grip_config = grip_config

        #Run the dispatcher to initialize servo position
        self.process_grip_change()

    def process_grip_change(self, percent):
        """Process the current grip config set in the class object."""
        for finger in self.grip_config:
            self.moveFinger(finger, (percent)*self.grip_config[finger])  

    def safe_shutdown(self):
        self.grip_config = hand_interface.grip_angles.lateral_power.value

        self.process_grip_change()

        print("[SERVO] Successfully killed servos.")
