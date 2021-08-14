import time
import os
import threading

from Status_Lights_Driver import slights
#testing new mendel workflow
#Status Lights initialization
statuslights = slights.slights_interface()
#Tell the user that we're in the startup sequence
slights_startup_thread = threading.Thread(target=statuslights.startup_wait, args=())
slights_startup_thread.start()

#import other files
# from os import ~.limbotics_github.transradial_development.Servo_driver.servo
from Servo_Driver import servo
from Camera_Interpreter import camera
from Muscle_Driver import muscle
from Hand_Classes import hand_interface
modes = hand_interface.modes
from State_Manager import state_manager

#Camera initialization
cam = camera.camera_interface()
# test
#Muscle sensor initialization
print("Debug muscle sensor? Y/N")
ans = input()
if(ans == "Y"):
    mi = muscle.muscle_interface(disconnect=True)
else:
    mi = muscle.muscle_interface()

    #Run through the muscle calibration sequence if necessary
    if not mi.disconnected:
        input_margin = 0.2 #%/100 margin for input val

        print("[CALIBRATION] Logging current channel 0 input as input threshold in 3...")
        time.sleep(1)
        print("2...")
        time.sleep(1)
        print("1...")
        time.sleep(1)
        mi.update_0_threshold()
        print("[CALIBRATION-CH0] Please perform a down squeeze, starting on 2, until 0.")
        print("[CALIBRATION-CH0] Ready?")
        time.sleep(2)
        print("3...")
        time.sleep(1)
        print("Squeeze now, and hold! 2...")
        time.sleep(1)
        print("1...")
        mi.update_0_max()
        # time.sleep(1) Not needed due to the integral/interval method in above function
        print("[CALIBRATION-CH0] Great! Thank you.")
        # print("[CALIBRATION-CH1] Logging current channel 1 input as input threshold in 3...")
        # time.sleep(1)
        # print("2...")
        # time.sleep(1)
        # print("1...")
        # time.sleep(1)
        # print("[CALIBRATION-CH1] Setting input threshold as ", str(mi.chan_1.value))
        # # mi.update_1_threshold((1+input_margin)*mi.chan_1.value)
        # print("[CALIBRATION-CH1] Please perform an up squeeze, starting on 2, until 0.")
        # print("[CALIBRATION-CH1] Ready?")
        # time.sleep(2)
        # print("3...")
        # time.sleep(1)
        # print("Squeeze now, and hold! 2...")
        # time.sleep(1)
        # print("1...")
        # mi.update_1_max()
        # time.sleep(1) Not needed due to the integral/interval method in above function
        # print("[CALIBRATION-CH1] Great! Thank you.")
        print("[CALIBRATION] Calibration sequence summary:")
        print("[CAL-CH0] CH0 input threshold: ", str(mi.analogThreshold_0), "CH0 max: ", str(mi.max_input_0))
        # print("[CAL-CH1] CH1 input threshold: ", str(mi.analogThreshold_1), "CH1 max: ", str(mi.max_input_1))

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
time_required_for_user_command = 0.1
new_pulse = (False, time.time())
old_pulse = new_pulse
servo_sleep = 0.05
program_T0 = time.time()
SM = state_manager.Mode_Manager()
#state_matrix = [reported_object, saved_state, user_command_detected, (time.time()-program_T0), (time.time()-program_T0)]

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
#Initialize hand positon/state lights
servs.grip_config = hand_interface.grips.openGrip.value
servo_thread = threading.Thread(target=servs.process_grip_change, args=())
servo_thread.start()
servo_thread.join()
# try:
#Initialize camera thread
cam_thread = threading.Thread(target=cam.camera_read_threader, args=())
cam_thread.start()
print("Main Program Start.")


#Debug user input variable
input_counter = time.time()

# servs.process_grip_change() #we're entering an initial grip, so no flag
# statuslights.set_status(False, hand_interface.input_types.none)

count = 0
while (cam_thread.is_alive() or (time.time() - SM._program_T0) > 15):
    count += 1
    time.sleep(0.01)
    print("\n")

    if(count%2==0): #Can modify the output rate of the state
        try:
            print("[DEBUG - MS] MyoSensor value: " , mi.AnalogRead())
        except Exception as e:
            print(SM.info)
            pass

    #Create new state matrix for current moment
    reported_object = cam.cam_data
    user_command_detected = mi.AnalogRead()

    #Set grip_picked to "" if it's not in the database of known objects
    object_id = True
    if(reported_object not in hand_interface.grips._value2member_map_ or (reported_object == hand_interface.grips.openGrip.value)):
        reported_object = SM.default_grip.value
        object_id = False
    
    # print("[DEBUG - GRIP] reported object open grip? " + str((reported_object == hand_interface.grips.openGrip.value)))
    # print("[DEBUG - OBJID] Object Identified? " + str(object_id))
    
    # print("[DEBUG - USER GRIP] TIME DIFFERENCE: " + str((new_state[3] - state_matrix[3])))
    # print("[DEBUG - USER GRIP] TIME BOOLEAN: " + str((new_state[3] - state_matrix[3]) >= time_required_for_user_command))

    #Check if the new state is a special one
    statuslights.set_status(object_id, user_command_detected, reported_object)

    #Pass the current system status to the state manager
    SM.master_state_tracker(user_command_detected)
    if (SM.current_mode == modes.AGS):
        print("[MT] In AGS Mode Processing")
        #Ensure the camera isn't paused
        if cam.temp_pause:
            cam.temp_pause = False

        #Let the servos know if the camera sees anything            
        servs.grip_config = reported_object

        # servo_thread.join()
        # servo_thread = threading.Thread(target=servs.process_grip_change, args=())
        # servo_thread.start()

        # statuslights.set_status(object_id, user_command_detected)
        #Wait for the servos to finish their current command
        # time.sleep(servo_sleep)
    elif (SM.current_mode == modes.GCM):
        print("[MT] In GCM Mode Processing")
        #Command the camera to stop processing inputs temporarily
        cam.temp_pause = True
        #Confirmed user commanding into reported object
        servs.grip_config = reported_object

        #servo_thread.join()
        servo_thread = threading.Thread(target=servs.process_grip_change, args=(True,mi.pmd))
        servo_thread.start()

        #Give servos some time to actuate
        time.sleep(servo_sleep)
    else:
        raise AttributeError("State Manager has no current mode defined.")

# except KeyboardInterrupt:
print("\nScript quit command detected - closing IO objects.")
statuslights.startup_complete = False
slights_startup_thread = threading.Thread(target=statuslights.startup_wait, args=())
slights_startup_thread.start()
# except Exception as e:
#     print(str(e))


#handLUTInst.loopHandLUTControl()
cam.end_camera_session()
# cam_thread.join() #Don't continue until the thread is closed 
servs.safe_shutdown()
time.sleep(0.5)

#Everything else is complete, so do status lights last
statuslights.startup_complete = True
slights_startup_thread.join()
statuslights.safe_shutdown()


print("Program ended.")
