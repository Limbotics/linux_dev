from adafruit_servokit import ServoKit

from enum import Enum


class handServoControl:
    """ This class provides a functional interface in order to command the servos for a given finger to move to a given position."""

    def __init__(self):

        #this class is the lookup table servo control because the functions kind of do everything already 
        #16 channel piHat
        self.kit = ServoKit(channels=16)

    def moveThumb(self, angle):
        self.kit.servo[fingers.thumb].angle = angle

    def moveIndex(self, angle):
        self.kit.servo[fingers.index].angle = angle

    def moveMiddle(self, angle):
        self.kit.servo[fingers.middle].angle = angle

    def moveRing(self, angle):
        self.kit.servo[fingers.ring].angle = angle

    def movePinky(self, angle):
        self.kit.servo[fingers.pinky].angle = angle


#https://www.w3schools.com/python/python_inheritance.asp

#this child class is the look up table and needs the most real world tuning
class handLUTControl(handServoControl):
    
    def __init__(self, grip_config=grips.openGrip):
        super().__init__()
        self.grip_config = grip_config

        #Initialize the dispatcher
        dispatch = {
            grips.openGrip: self.openGrip,
            grips.fist:     self.closeGrip,
            grips.pencil:   self.pencilGrip,
            grips.cup:      self.cupGrip,
        }
        self.dispatch = dispatch

    def openGrip(self):
        self.moveThumb(0)
        self.moveIndex(0)
        self.moveMiddle(0)
        self.moveRing(0)
        self.movePinky(0)
    
    def closeGrip(self):
        self.moveThumb(180)
        self.moveIndex(180)
        self.moveMiddle(180)
        self.moveRing(180)
        self.movePinky(180)

    def pencilGrip(self):
        self.moveThumb(150)
        self.moveIndex(120)
        self.moveMiddle(180)
        self.moveRing(180)
        self.movePinky(180)

    def cupGrip(self):
        self.moveThumb(140)
        self.moveIndex(160)
        self.moveMiddle(160)
        self.moveRing(160)
        self.movePinky(160)

    def process_command(self):
        self.dispatch[self.grip_config]()