import time
import os
import threading

from Status_Lights_Driver import slights

#Status Lights initialization
statuslights = slights.slights_interface()
#Tell the user that we're in the startup sequence
slights_startup_thread = threading.Thread(target=statuslights.startup_wait, args=())
slights_startup_thread.start()

from adafruit_servokit import ServoKit

#import other files
# from os import ~.limbotics_github.transradial_development.Servo_driver.servo
from Servo_Driver import servo
from Camera_Interpreter import camera
from Muscle_Driver import muscle
from Hand_Classes import hand_interface


#Camera initialization
cam = camera.camera_interface()

#Muscle sensor initialization
mi = muscle.muscle_interface()

#Servo control initialization
servs = servo.handLUTControl()

outValue = 0
def mapAnalogtoServo():
     #servs is object function to move is servs.moveFinger(self, finger, angle)
     #8000 in to 13000
     outValue = (mi.AnalogRead()-8000)*180/5000
     servs.moveFinger(0, int(outValue))
     servs.moveFinger(1, int(outValue))
     servs.moveFinger(2, int(outValue))


count = 0
status_T0 = 0
previous_grip = ""
grip_picked = ""   #
user_activated_grip = False
user_activated_grip_T0 = time.time()
loop_time_step = 0.01
# delta_required_for_status_change = 115*(loop_time_step/0.001) #Units of n are in milliseconds, regardless of loop time step
delta_required_for_status_change = 100 #Units of n are in milliseconds, regardless of loop time step

#Quit the status lights loading period
statuslights.startup_complete = True
slights_startup_thread.join()

print("Main Program Start.")
try:
    #Initialize camera thread
    cam_thread = threading.Thread(target=cam.camera_read_threader, args=())
    cam_thread.start()
    while ((count < 10000000) and cam_thread.is_alive()):
        grip_picked = cam.cam_data
        is_object = cam.object_spotted
        #Set grip_picked to "" if it's not in the database of known objects
        if(grip_picked not in hand_interface.grips._value2member_map_):
            grip_picked = ""
            is_object = False

        # print("MyoSensor value: " , mi.AnalogRead())

        # mapAnalogtoServo()
        if mi.triggered():
            user_gripping = True
            #insert code to grip (for now lets overide object detection, but later just if obj detect and mi.triggered() then grip)
        else:
            user_gripping = False

        if(is_object and (count%10 ==0)):
            # print("MyoSensor value: " , mi.AnalogRead())
            print("[INFO] Main thread spots an object: " + str(grip_picked) + " .\t" + str(count))
            # print("[INFO] State: (grip_picked: "+ grip_picked+", user_gripping: "+ str(user_gripping)+"). Lights: " + str(statuslights.status))
        elif(count%10==0):
            print("MyoSensor value: " , mi.AnalogRead())
            print("[INFO] Main thread, no object.\t" + str(count))
            # print("[INFO] State: (grip_picked: "+ grip_picked+", user_gripping: "+ str(user_gripping)+") Lights: " + str(statuslights.status))

        #Only allow a state update no quicker than every delta time
        if((abs(count - status_T0) > delta_required_for_status_change)): # and servs.authorized_to_change_grips()
            if (not user_activated_grip and not user_gripping): #If the user hasn't picked anything, computer has priority
                # print("No activation, no gripping")
                if (grip_picked is not previous_grip):
                    if (grip_picked == ""):                     #If no object, set it to the open grip value. Otherwise, just keep it
                        grip_picked = hand_interface.grips.openGrip.value
                    servs.grip_config = grip_picked
                     # servo_command = threading.Thread(target = servs.process_grip_change, args=())
                    servs.process_grip_change()
                    statuslights.set_status(user_activated_grip, user_gripping)
            elif(user_activated_grip and not user_gripping): #User previously activated this grip, so stay here
                # print("Activation, no gripping")
                pass
            elif(user_activated_grip and user_gripping): #User gripping after activating a grip is the exit command
                # print("Activation, gripping")
                if((time.time() - user_activated_grip_T0) > 1): #Remove user priority
                    user_activated_grip = False
                    if (grip_picked == ""):                     #If no object, set it to the open grip value. Otherwise, just keep it
                        grip_picked = hand_interface.grips.openGrip.value
                    servs.grip_config = grip_picked
                    # servo_command = threading.Thread(target = servs.process_grip_change, args=())
                    servs.process_grip_change() #we're leaving a grip in this state, so don't pass user grip flag
                    statuslights.set_status(user_activated_grip, user_gripping)
            elif(not user_activated_grip and user_gripping):
                # print("No Activation, gripping")
                if(grip_picked != ""):
                    user_activated_grip = True
                    servs.grip_config = grip_picked
                    # servo_command = threading.Thread(target = servs.process_grip_change, args=())
                    servs.process_grip_change(user_grip=user_activated_grip)
                    statuslights.set_status(user_activated_grip, user_gripping)
            # print("Current grip: " + grip_picked)

            #Update status lights
            # 
            status_T0 = count

            #Save grip pick
            previous_grip = grip_picked

        statuslights.set_status(is_object, user_gripping)
        time.sleep(loop_time_step)
        count += 1
except KeyboardInterrupt:
    print("\nScript quit command detected - closing IO objects.")
    statuslights.startup_complete = False
    slights_startup_thread = threading.Thread(target=statuslights.startup_wait, args=())
    slights_startup_thread.start()

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

#Everything else is complete, so do status lights last
statuslights.startup_complete = True
slights_startup_thread.join()
statuslights.safe_shutdown()


print("Program ended.")
