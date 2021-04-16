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
# mi = muscle.muscle_interface()

#Servo control initialization
servs = servo.handLUTControl()

outValue = 0
# def mapAnalogtoServo():
#      #servs is object function to move is servs.moveFinger(self, finger, angle)
#      #8000 in to 13000
#      outValue = (mi.AnalogRead()-8000)*180/5000
#      servs.moveFinger(0, int(outValue))
#      servs.moveFinger(1, int(outValue))
#      servs.moveFinger(2, int(outValue))
    
#Save the state of the arm
reported_object = ""
saved_state = False
user_command_detected = False
time_required_for_open_state = 5
time_required_for_any_state = 0.25
time_required_for_user_command = 2
servo_sleep = 0.25
program_T0 = time.time()
state_matrix = [reported_object, saved_state, user_command_detected, (time.time()-program_T0), (time.time()-program_T0)]

#Quit the status lights loading period
statuslights.startup_complete = True
slights_startup_thread.join()

#while true
    #Create a new state matrix for the current moment
        #Camera read in
        #user command read in
        #save to new state matrix

    #Check if we're in a special state that overrides the time required to change states
    #User input with saved state? Remove saved state, command servos to open position
    #User input with no saved state? 
        #Reported object? Set saved state, command servos to fully closed position
        #No reported object? Flash the lights to let user know we don't see anything

    #Time passed to permit generic state change?
        #reported object? 
            #Saved state? Do nothing
            #No saved state? Initialize grip for this object
        #No user input, no reported object?
            #Set servos to open position 

try:
    #Initialize camera thread
    cam_thread = threading.Thread(target=cam.camera_read_threader, args=())
    cam_thread.start()
    print("Main Program Start.")
    #Initialize hand positon/state lights
    servs.grip_config = hand_interface.grips.openGrip.value

    servs.process_grip_change() #we're entering an initial grip, so no flag
    statuslights.set_status(False, False)

    count = 0
    while (cam_thread.is_alive()):
        count += 1
        time.sleep(0.01)

        if(count%10==0):
            # print("[DEBUG - MS] MyoSensor value: " , mi.AnalogRead())
            print("[INFO - State]  " + str(state_matrix))

        #Testing user flex
        start_loop = 1000
        end_loop = 2000
        user_command_detected = False
        if(count > start_loop and count < end_loop):
            user_command_detected = True
            print("[DEBUG - MS] Sending user input... cutting in L-" + str(end_loop-count))
        elif(count < start_loop):
            print("[DEBUG - MS] No user input - L-" + str(start_loop-count))
        else:
            print("[DEBUG - MS] Resetting user input sequence")
            count = 0

        #Create new state matrix for current moment
        reported_object = cam.cam_data
        # user_command_detected = mi.triggered()
        # user_command_detected = False #Just for testing purposes

        #Set grip_picked to "" if it's not in the database of known objects
        object_id = True
        if(reported_object not in hand_interface.grips._value2member_map_ or (reported_object == hand_interface.grips.openGrip.value)):
            reported_object = hand_interface.grips.openGrip.value
            object_id = False
        
        print("[DEBUG - GRIP] reported object open grip?" + str((reported_object == hand_interface.grips.openGrip.value)))
        print("[DEBUG - OBJID] Object Identified? " + str(object_id))
        
        new_state = [reported_object, False, user_command_detected, (time.time()-program_T0), (time.time()-program_T0)]

        #Check if the new state is a special one
        if (user_command_detected and state_matrix[1] and ((new_state[3] - state_matrix[3]) > time_required_for_user_command)): #User trying to leave current state
            #Update the servo current grip set
            servs.grip_config = reported_object
            servs.process_grip_change() #we're leaving a grip in this state, so don't pass user grip flag
            statuslights.set_status(object_id, user_command_detected)
            #Wait for the servos to finish their current command
            time.sleep(servo_sleep)
            #Update current state
            state_matrix = new_state
        elif(user_command_detected and not state_matrix[1] and ((new_state[3] - state_matrix[3]) > time_required_for_user_command)):
            #Check if the user is commanding us into a reported object
            if(not object_id):
                print("[DEBUG - STATE] Trying to enter new save state")
                #Repair init new state matrix 
                new_state[1] = True
                #Confirmed user commanding into reported object
                servs.grip_config = reported_object

                servs.process_grip_change(user_grip=True) #we're entering a grip, so pass flag
                statuslights.set_status(object_id, user_command_detected)
                #Wait for the servos to finish their current command
                time.sleep(servo_sleep)
                #Update current state
                state_matrix = new_state
        elif(not state_matrix[1]): #No user command processed, so proceed to other checks if we're not in a saved state
            #Time check passed, so maybe allow new camera command
            if((object_id) and ((new_state[3] - state_matrix[3]) > time_required_for_any_state)): #If we spot an object and we're not gripped currently
                #Confirmed user commanding into reported object
                servs.grip_config = reported_object

                servs.process_grip_change() #we're entering an initial grip, so no flag
                statuslights.set_status(object_id, user_command_detected)
                #Wait for the servos to finish their current command
                time.sleep(servo_sleep)
                #Update current state
                state_matrix = new_state
            elif((not object_id) and ((new_state[3] - state_matrix[3]) > time_required_for_open_state)):
                #We see nothing and delta time has passed, so ensure we're in the open position
                #Confirmed user commanding into reported object
                servs.grip_config = reported_object

                servs.process_grip_change() #we're entering an initial grip, so no flag
                statuslights.set_status(object_id, user_command_detected)
                #Skip wait b/c it's just open grip
                # time.sleep(servo_sleep)
                #Update current state
                state_matrix = new_state

        state_matrix[4] = (time.time()-program_T0)

except KeyboardInterrupt:
    print("\nScript quit command detected - closing IO objects.")
    statuslights.startup_complete = False
    slights_startup_thread = threading.Thread(target=statuslights.startup_wait, args=())
    slights_startup_thread.start()


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
