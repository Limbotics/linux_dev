import time

from adafruit_servokit import ServoKit

#import other files
from .Servo_Driver.servo import *
##JERED HELP ME HOW TF DO U IMPORT OTHER FILES
## OK ok I'll help lol

handLUTInst = handLUTControl()

while True:
    handLUTInst.loopHandLUTControl()

    #update handLUTInst grips using this:
    handLUTInst.grip_config = "pencil"

