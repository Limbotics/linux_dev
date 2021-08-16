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
        print("[CALIBRATION] Calibration sequence summary:")
        print("[CAL-CH0] CH0 input threshold: ", str(mi.analogThreshold_0), "CH0 max: ", str(mi.max_input_0))
        # print("[CAL-CH1] CH1 input threshold: ", str(mi.analogThreshold_1), "CH1 max: ", str(mi.max_input_1))

#Servo control initialization
servs = servo.handLUTControl()

outValue = 0
    
#Save the state of the arm
reported_object = ""
saved_state = False
user_command_detected = False
time_required_for_open_state = 5
time_required_for_any_state = 0.25
time_required_for_user_command = 0.1
servo_sleep = 0.05
program_T0 = time.time()
SM = state_manager.Mode_Manager()

#Quit the status lights loading period
statuslights.startup_complete = True
slights_startup_thread.join()

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

count = 0
output_delay = time.time()
while (cam_thread.is_alive()):
    count += 1

    #Create new state matrix for current moment
    reported_object = cam.cam_data
    user_command_detected = mi.AnalogRead()

    #Set grip_picked to "" if it's not in the database of known objects
    object_id = True
    if(reported_object not in hand_interface.grips._value2member_map_ or (reported_object == hand_interface.grips.openGrip.value)):
        reported_object = SM.default_grip.value
        object_id = False
    
    #Check if the new state is a special one
    statuslights.set_status(object_id, user_command_detected, reported_object)

    #Generate the nice output
    if (time.time() - output_delay) > 0.05:
        data_list = {}
        data_list["program_time"] = str(round((time.time() - SM._program_T0), 2))
        data_list["state"] = str(SM.current_mode)
        data_list["spotted_object"] = str(cam.cam_data)
        data_list["inference_time"] = str(round((1/cam.inference_time), 1))
        data_list["spotted_object_score"] = str(round((100*cam.cam_data_score), 2))
        data_list["muscle_input"] = str(int(mi.ads.read_adc(0, gain=1)))
        data_list["muscle_input_percent"] = str(100*mi.pmd)
        data_list["muscle_input_type"] = str(mi.last_input[0])
        data_list["servo_grip_loaded"] = str(servs.grip_config)
        data_list["vibes"] = str(statuslights.vibe_status)
        SM.nice_output(data_list)

        output_delay = time.time()
    

    #Pass the current system status to the state manager
    SM.master_state_tracker(user_command_detected)
    if (SM.current_mode == modes.AGS):
        # print("[MT] In AGS Mode Processing")
        #Ensure the camera isn't paused
        if cam.temp_pause:
            cam.temp_pause = False

        #Let the servos know if the camera sees anything            
        servs.grip_config = reported_object

    elif (SM.current_mode == modes.GCM):
        # print("[MT] In GCM Mode Processing")
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

cam.end_camera_session()
# cam_thread.join() #Don't continue until the thread is closed 
servs.safe_shutdown()
time.sleep(0.5)

#Everything else is complete, so do status lights last
statuslights.startup_complete = True
slights_startup_thread.join()
statuslights.safe_shutdown()

print("Program ended.")




