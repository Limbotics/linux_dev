import time
import os
import threading
import tty
import sys


from Status_Lights_Driver import slights
#testing new mendel workflow
#Status Lights initialization
statuslights = slights.slights_interface()

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

#Tell the user that we're ready for their input
slights_startup_thread = threading.Thread(target=statuslights.startup_wait, args=())
slights_startup_thread.start()
#Muscle sensor initialization
print("Debug muscle sensor? Y/N")
ans = input()
if(ans == "Y"):
    mi = muscle.muscle_interface(disconnect=True)
else:
    mi = muscle.muscle_interface()

    #Run through the muscle calibration sequence if necessary
    if not mi.disconnected:

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
        print("[CALIBRATION] Calibration sequence summary:")
        print("[CAL-CH0] CH0 input threshold: ", str(mi.analogThreshold_0), "CH0 max: ", str(mi.max_input_0))
        time.sleep(2)
        # print("[CAL-CH1] CH1 input threshold: ", str(mi.analogThreshold_1), "CH1 max: ", str(mi.max_input_1))

#Start the emg read thread
emg_thread = threading.Thread(target=mi.AnalogRead, args=())
emg_thread.start()

#Servo control initialization
servs = servo.handLUTControl()

#Save the state of the arm
reported_object = ""
user_command_detected = False
SM = state_manager.Mode_Manager()
#Create user input program killer watchdog
program_killer_thread = threading.Thread(target=SM.killer_watcher, args=())
program_killer_thread.start()

#Quit the status lights loading period
statuslights.startup_complete = True
slights_startup_thread.join()

#Initialize hand positon/state lights
servs.grip_config = hand_interface.grip_angles.lateral_power.value
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

count = 0
output_delay = time.time()
while (cam_thread.is_alive() and not SM.killed):
    
    count += 1

    #Create new state matrix for current moment
    reported_object = cam.cam_data
    user_command_detected = mi.last_input[0]

    #Set grip_picked to "" if it's not in the database of known objects
    object_id = True
    if(reported_object == ""):
        reported_object = SM.default_grip
        object_id = False
    grip_name = hand_interface.grips.object_to_grip_mapping.value[reported_object]
    
    #Check if the new state is a special one
    statuslights.set_status(object_id, user_command_detected, reported_object)

    #Generate the nice output
    if (time.time() - output_delay) > 0.25:
        data_list = {}
        data_list["program_time"] = str(round((time.time() - SM._program_T0), 2))
        data_list["state"] = str(SM.current_mode)
        data_list["spotted_object"] = str(cam.cam_data)
        data_list["other_cam_data"] = cam.other_cam_data 
        data_list["inference_time"] = str(round((1/cam.inference_time), 1))
        data_list["spotted_object_score"] = str(round((100*cam.cam_data_score), 2))
        data_list["muscle_input"] = str(int(mi.filtered_data[-1]))
        data_list["muscle_input_percent"] = str(100*mi.pmd)
        data_list["muscle_input_type"] = str(mi.last_input[0])
        data_list["servo_grip_loaded"] = str(grip_name)
        data_list["vibes"] = str(statuslights.vibe_status)
        data_list["smoothing_time"] = str(mi.smoothing_time)
        SM.nice_output(data_list)

        output_delay = time.time()
    
    #Pass the current system status to the state manager
    SM.master_state_tracker(user_command_detected)
    if (SM.current_mode == modes.AGS):
        # print("[MT] In AGS Mode Processing")
        #Ensure the camera isn't paused
        if cam.temp_pause:
            cam.temp_pause = True #TODO: Set back

        #Let the servos know if the camera sees anything         
        grip_name = hand_interface.grips.object_to_grip_mapping.value[reported_object]
        servs.grip_config = grip_name

    elif (SM.current_mode == modes.GCM):
        # print("[MT] In GCM Mode Processing")
        #Command the camera to stop processing inputs temporarily
        cam.temp_pause = True
        #Confirmed user commanding into reported object
        # grip_name = hand_interface.grips.object_to_grip_mapping.value[reported_object]
        # servs.grip_config = grip_name

        #servo_thread.join()
        servo_thread = threading.Thread(target=servs.process_grip_change, args=(mi.pmd,))
        servo_thread.start()
    else:
        raise AttributeError("State Manager has no current mode defined.")

# except KeyboardInterrupt:
print("\nScript quit command detected - closing IO objects.")
statuslights.startup_complete = False
mi.shutdown()

cam.end_camera_session()
# cam_thread.join() #Don't continue until the thread is closed 
servs.safe_shutdown()
time.sleep(0.5)

#Everything else is complete, so do status lights last
statuslights.startup_complete = True
statuslights.safe_shutdown()

print("Program ended.")
