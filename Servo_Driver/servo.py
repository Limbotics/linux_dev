from adafruit_servokit import ServoKit
#https://learn.adafruit.com/adafruit-16-channel-pwm-servo-hat-for-raspberry-pi/using-the-python-library#controlling-servos-3013804-22

from enum import Enum

import sys
import os
sys.path.append(os.path.abspath('../Hand_Classes'))
#from hand_interface import fingers, grips
from Hand_Classes import hand_interface
fingers = hand_interface.fingers
grips = hand_interface.grips
grip_finger_angles = hand_interface.grip_finger_angles

class handServoControl:
    """ This class provides a functional interface in order to command the servos for a given finger to move to a given position."""

    def __init__(self):

        #this class is the lookup table servo control because the functions kind of do everything already 
        #16 channel piHat
        self.kit = ServoKit(channels=16)

        #Initialize stored angles
        self.angles = {
            fingers.thumb: 0,
            fingers.index: 0,
            fingers.middle: 0,
            fingers.ring: 0,
            fingers.pinky: 0
        }

    def moveFinger(self, finger, angle):
        self.kit.servo[finger].angle = angle
        self.angles[finger] = angle

    def get_angle_set(self):
        return self.angles

#https://www.w3schools.com/python/python_inheritance.asp

#this child class is the look up table and needs the most real world tuning
class handLUTControl(handServoControl):
    
    def __init__(self, grip_config=grips.openGrip.value):
        super().__init__()
        self.grip_config = grip_config

        #Initialize the dispatcher
        dispatch = {
            grips.openGrip.value: grip_finger_angles.openGrip,
            grips.fist.value:     grip_finger_angles.closeGrip,
            grips.pencil.value:   grip_finger_angles.pencil,
            grips.cup.value:      grip_finger_angles.cup,
        }
        self.dispatch = dispatch

        #Run the dispatcher
        self.process_command()

    """Process the current grip config set in the class object."""
    def process_command(self):
        finger_angles = self.dispatch[self.grip_config]
        for finger in finger_angles:
            self.moveFinger(finger, finger_angles[finger])  

    """Checks if all the angles are set to zero by the user."""
    def authorized_to_change_grips(self):
        return 
