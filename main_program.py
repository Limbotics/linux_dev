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
status_T0 = 0
delta_required_for_status_change = 35
print("Main Program Start.")
while (count < 1000):
    try:
        grip_picked, _, _, is_object =  cam.read_cam() #NOTE: grip_picked is just the QR code data being read
        user_gripping = False
        if((abs(count - status_T0) > delta_required_for_status_change) and servs.authorized_to_change_grips()):
            #Update grip configuration, if we should
            #servs.grip_config = grip_picked
            #servs.process_grip_change()

            #Update status lights
            statuslights.set_status(is_object, user_gripping)
            status_T0 = count

            print("Changed grip configuration to %s", grip_picked)
        
        time.sleep(0.001)
        count += 1
    except KeyboardInterrupt:
        print("\nScript quit command detected - closing IO objects.")
        break
    #print(count)
#Determine the current state we're in 
    #No input from user, unfrozen state -> Permission to identify objects, change grip configuration after deltaT of object in view
    #No object detected & not currently in grasp mode -> Continue looking for object
    #No object detected & currently in grasp mode     -> User is actuating current grasp, do not change current grip
    #Object detected & not currently in grasp mode    -> Select grip from database, command servos to new grip
    #Object detected & currently in grasp mode        -> User is actuating current grasp, do not change current grip

#handLUTInst.loopHandLUTControl()
cam.end_camera_session()
statuslights.safe_shutdown()

print("No errors occured.")
