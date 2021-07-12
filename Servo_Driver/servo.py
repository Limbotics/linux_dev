from adafruit_servokit import ServoKit
#https://learn.adafruit.com/adafruit-16-channel-pwm-servo-hat-for-raspberry-pi/using-the-python-library#controlling-servos-3013804-22
#LINUX FIX:
# #https://gitmemory.com/issue/adafruit/Adafruit_Blinka/328/672356503
from enum import Enum
import time

import sys
import os
sys.path.append(os.path.abspath('../Hand_Classes'))

#Import interface enums from hand_interface
from Hand_Classes import hand_interface
fingers = hand_interface.fingers
grips = hand_interface.grips
grip_finger_angles = hand_interface.grip_finger_angles

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

        #Initialize stored angles
        self.angles = {
            fingers.thumb: 0,
            fingers.index: 0,
            fingers.middle: 0,
            fingers.ring: 0,
            fingers.pinky: 0
        }

    def moveFinger(self, finger, angle):
        """Command a given finger to a certain angle.
        
        Parameters:
            finger (int): One of the hand_interfaces.fingers values to dictate which channel to command a servo.

            angle (int):  The angle to which to command the given servo to.

        """
        self.kit.servo[finger].angle = angle
        self.angles[finger] = angle
        time.sleep(0.1)

#https://www.w3schools.com/python/python_inheritance.asp

#this child class is the look up table and needs the most real world tuning
class handLUTControl(handServoControl):
    """
    High-level servo control in terms of hand manipulation.
      
    Attributes:
        dispatch (dict): Correlates different grips to their respective servo angle definitions.
        grip_config (string): The current hand_interfaces.grips (values) parameter the system is set to.
        
    """
    
    def __init__(self, grip_config=grips.openGrip.value):
        super().__init__()
        self.grip_config = grip_config

        #Initialize the dispatcher
        dispatch = {
            grips.openGrip.value: grip_finger_angles.openGrip.value,
            grips.small.value:     grip_finger_angles.small.value,
            grips.bottle.value:   grip_finger_angles.bottle.value,
            grips.bowl.value:      grip_finger_angles.bowl.value,
            grips.test.value:       grip_finger_angles.test.value,
            grips.cell.value:    grip_finger_angles.cell_phone.value
        }
        user_dispatch = {
            grips.bottle.value: grip_finger_angles.bottle_full_closed.value,
            grips.small.value:     grip_finger_angles.small_full_closed.value,
            grips.test.value: grip_finger_angles.test.value,
            grips.cell.value:    grip_finger_angles.cell_phone_closed.value
        }
        self.user_dispatch = user_dispatch
        self.dispatch = dispatch

        #Run the dispatcher to initialize servo position
        self.process_grip_change()

    def process_grip_change(self, user_grip=False):
        """Process the current grip config set in the class object."""
        try:
            if(not user_grip):
                #Use the dispatcher to correlate the current grip to the angles for that grip
                finger_angles = self.dispatch[self.grip_config]

                #Iterate through the fingers and set them to their respective angle
                for finger in finger_angles:
                    self.moveFinger(finger, finger_angles[finger])  
            else:
                #Use the dispatcher to correlate the current grip to the angles for that grip
                finger_angles = self.user_dispatch[self.grip_config]

                #Iterate through the fingers and set them to their respective angle
                for finger in finger_angles:
                    self.moveFinger(finger, finger_angles[finger])  
        except Exception as e:
            # print("[DEBUG] User command for no specific object")
            pass

    def user_input_actuation(self, percent):
        """Convert myoelectric input into servo actuation for the current grip."""
        pass

    def __list_diff(self, li1, li2):
        """Math helper function for authorized_to_change_grips"""
        return (list(list(set(li1)-set(li2)) + list(set(li2)-set(li1))))

    def authorized_to_change_grips(self):
        """Checks if all the angles are set to zero by the user, implying the computer has priority to change the grip."""
        
        #Get the difference between the current list of angles and the initial angles in the current grip
        delta_vals = self.__list_diff(list(self.angles.values()), list(self.dispatch[self.grip_config].values()))

        #return True if all are zero, or False if any are not zero.
        return all(value == 0 for value in delta_vals)

    def safe_shutdown(self):
        self.grip_config = grips.openGrip.value

        self.process_grip_change()
