import time
import os

from adafruit_servokit import ServoKit

#import other files
# from os import ~.limbotics_github.transradial_development.Servo_driver.servo
from Servo_Driver import servo
from Camera_Interpreter import camera

handLUTInst = servo.handLUTControl()

#while True:
    #Determine the current state we're in 
        #No object detected & not currently in grasp mode -> Continue looking for object
        #No object detected & currently in grasp mode     -> User is actuating current grasp, do not change current grip
        #Object detected & not currently in grasp mode    -> Select grip from database
        #Object detected & currently in grasp mode        -> User is actuating current grasp, do not change current grip

#handLUTInst.loopHandLUTControl()

#update handLUTInst grips using this:
#handLUTInst.grip_config = "pencil"

print("No errors occured.")
