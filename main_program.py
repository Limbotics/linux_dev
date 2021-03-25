import time
import os

from adafruit_servokit import ServoKit

#import other files
# from os import ~.limbotics_github.transradial_development.Servo_driver.servo
from Servo_Driver import servo
from Camera_Interpreter import camera
from Muscle_Driver import muscle
from Status_Lights_Driver import slights

#Camera initialization
cam = camera.camera_interface()

#Muscle sensor initialization
mi = muscle.muscle_interface()

#Servo control initialization
#servs = servo.handLUTControl()

#Status Lights initialization
statuslights = slights.slights_interface()

count = 0
while (count < 100):
    grip_picked, _, _, is_object =  cam.read_cam() #NOTE: grip_picked is just the QR code data being read
    user_gripping = False
    # if(grip_picked):
    #     servs.grip_config = grip_picked
    #     servs.process_command()
    # else:
    #     servs.process_command()
    statuslights.set_status(is_object, user_gripping)
    time.sleep(0.01)
    count += 1
    print(count)
#Determine the current state we're in 
    #No input from user, unfrozen state -> Permission to identify objects, change grip configuration after deltaT of object in view
    #No object detected & not currently in grasp mode -> Continue looking for object
    #No object detected & currently in grasp mode     -> User is actuating current grasp, do not change current grip
    #Object detected & not currently in grasp mode    -> Select grip from database, command servos to new grip
    #Object detected & currently in grasp mode        -> User is actuating current grasp, do not change current grip

#handLUTInst.loopHandLUTControl()
cam.end_camera_session()
#update handLUTInst grips using this:
#

print("No errors occured.")
