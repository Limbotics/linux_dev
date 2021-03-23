import time
import os

from adafruit_servokit import ServoKit

#import other files
# from os import ~.limbotics_github.transradial_development.Servo_driver.servo
from Servo_Driver import servo
from Camera_Interpreter import camera
from Muscle_Driver import muscle

#Camera initialization
cam = camera.camera_interface()

#Muscle sensor initialization
mi = muscle.muscle_interface()

#Servo control initialization
#servs = servo.handLUTControl()

while True:
    cam.read_cam_display_out()

    time.sleep(1)
    #Determine the current state we're in 
        #No input from user, unfrozen state -> Permission to identify objects, change grip configuration after deltaT of object in view
        #No object detected & not currently in grasp mode -> Continue looking for object
        #No object detected & currently in grasp mode     -> User is actuating current grasp, do not change current grip
        #Object detected & not currently in grasp mode    -> Select grip from database, command servos to new grip
        #Object detected & currently in grasp mode        -> User is actuating current grasp, do not change current grip

#handLUTInst.loopHandLUTControl()

#update handLUTInst grips using this:
#handLUTInst.grip_config = "pencil"

print("No errors occured.")
