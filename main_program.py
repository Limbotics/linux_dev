import time
import os
import threading

from adafruit_servokit import ServoKit

#import other files
# from os import ~.limbotics_github.transradial_development.Servo_driver.servo
from Servo_Driver import servo
from Camera_Interpreter import camera
from Muscle_Driver import muscle
from Status_Lights_Driver import slights
from Hand_Classes import hand_interface

#Camera initialization
cam = camera.camera_interface()

#Muscle sensor initialization
mi = muscle.muscle_interface()

#Servo control initialization
servs = servo.handLUTControl()

#Status Lights initialization
statuslights = slights.slights_interface()

count = 0
status_T0 = 0
previous_grip = ""
grip_picked = ""
user_activated_grip = False
user_activated_grip_T0 = time.time()
loop_time_step = 0.001
delta_required_for_status_change = 250*(loop_time_step/0.001) #Units of n are in milliseconds, regardless of loop time step
print("Main Program Start.")
try:
    #Initialize camera thread
    cam_thread = threading.Thread(target=cam.camera_read_threader, args=())
    cam_thread.start()
    while ((count < 10000000) and cam_thread.is_alive()):
        grip_picked = cam.cam_data
        is_object = cam.object_spotted

        if mi.triggered():
            print("MyoSensor Triggered, value: " , mi.AnalogRead())
            user_gripping = True
            #insert code to grip (for now lets overide object detection, but later just if obj detect and mi.triggered() then grip)
        else:
            user_gripping = False

        if(is_object and (count%250 ==0)):
            print("Main thread spots an object! " + str(count))
        elif(count%250==0):
            print("Main thread, no object." + str(count))
        if((abs(count - status_T0) > delta_required_for_status_change)): # and servs.authorized_to_change_grips()
            #Update grip configuration, if we should
            if (not user_activated_grip and not user_gripping): #If the user hasn't picked anything, computer has priority
                if (grip_picked is not previous_grip):
                    if (grip_picked == ""):                     #If no object, set it to the open grip value. Otherwise, just keep it
                        grip_picked = hand_interface.grips.openGrip.value
                    servs.grip_config = grip_picked
                     # servo_command = threading.Thread(target = servs.process_grip_change, args=())
                    servs.process_grip_change()
            elif(user_activated_grip and not user_gripping): #User wants to stay in this grip, 
                pass
            elif(user_activated_grip and user_gripping): #User might be wanting to quit grip, so check delta time
                if((time.time() - user_activated_grip_T0) > 0.5): #Remove user priority
                    user_activated_grip = False
            elif(not user_activated_grip and user_gripping):
                user_activated_grip = True
                servs.grip_config = grip_picked
                     # servo_command = threading.Thread(target = servs.process_grip_change, args=())
                servs.process_grip_change()

            #Update status lights
            # statuslights.set_status(is_object, user_gripping)
            status_T0 = count

            #Save grip pick
            previous_grip = grip_picked

        statuslights.set_status(is_object, user_gripping)
        time.sleep(loop_time_step)
        count += 1
except KeyboardInterrupt:
    print("\nScript quit command detected - closing IO objects.")
    #print(count)
#Determine the current state we're in 
    #No input from user, unfrozen state -> Permission to identify objects, change grip configuration after deltaT of object in view
    #No object detected & not currently in grasp mode -> Continue looking for object
    #No object detected & currently in grasp mode     -> User is actuating current grasp, do not change current grip
    #Object detected & not currently in grasp mode    -> Select grip from database, command servos to new grip
    #Object detected & currently in grasp mode        -> User is actuating current grasp, do not change current grip

#handLUTInst.loopHandLUTControl()
cam.end_camera_session()
cam_thread.join() #Don't continue until the thread is closed 
servs.safe_shutdown()
time.sleep(0.5)
statuslights.safe_shutdown()


print("Program ended.")
