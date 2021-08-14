""" This package provides the interface for the system to change the status lights."""
from typing import NoReturn, Sequence
from periphery import GPIO
from periphery import PWM
import time

import sys
import os
sys.path.append(os.path.abspath('../Hand_Classes')) # Adds higher directory to python modules path.

from Hand_Classes import hand_interface
grips = hand_interface.grips
input_types = hand_interface.input_types
timers = hand_interface.input_constants
modes = hand_interface.modes

from enum import Enum

class Mode_Manager():
    _program_T0 = time.time()
    _reported_object = ""
    _user_command_detected = False
    #These work together in conjunction to track unique user inputs
    _user_input_time = 0 #The timestamp for when the user started this input
    _previous_user_input_time = 0 #The timestamp for when the user started previous input
    _mode_time = time.time() #The timestamp at which the current mode was entered
    _run_time = time.time() - _program_T0  #The total program runtime
    """
    Manages and tracks the current mode of the system. Methods provide checking for if a mode change is valid given certain parameters. 

      
    Attributes:
        
        
    """

    def __init__(self):

        #Maps top modes to each other for switching back and forth
        self.top_modes = {
            modes.Neutral: modes.AGS,
            modes.AGS: modes.Neutral
        }

        #Initialize the top mode as Neutral
        self._top_mode = modes.AGS
        self._current_mode = modes.AGS

        #Define the default grip 
        self._default_grip = grips.openGrip

        #Maps how system inputs map to events
        self.inputs_to_events_mapping = {
            input_types.down: self.activate_gcm,  #Down holding always activates GCM
            input_types.none: self.no_input_manager
        }

    @property
    def info(self):
        # Build a human-readable format of the current system state
        return "Current mode: ", self.current_mode, " Top mode: ", self.top_mode, " User input: ", self.user_command_detected, "\t Mode time: ", str(self.mode_time)
    
    ######### Mode management
    @property
    def top_mode(self):
        return self._top_mode

    @property
    def current_mode(self):
        return self._current_mode

    @current_mode.setter
    def current_mode(self, new_mode):
        print("[MODE CHANGE] The mode is changing to ", str(new_mode), " from ", self._current_mode)
        self.set_mode_time()
        self._current_mode = new_mode

    #Toggles the top mode, additionally, the top mode MUST change with the current mode.
    def toggle_top_mode(self):
        self._top_mode = self.top_modes[self._top_mode]
        self.current_mode = self._top_mode
        print("[TOP MODE TOGGLE] Successfully changed top/current mode to ", str(self.current_mode))

    ######### Param management
    @property
    def reported_object(self):
        return self._reported_object

    @reported_object.setter
    def reported_object(self, new_object):
        self._reported_object = new_object

    @property
    def default_grip(self):
        return self._default_grip

    @default_grip.setter
    def default_grip(self, new_default):
        #Set the current mode to top mode
        if self.current_mode == modes.Cycle_Grip and self.is_unique_input:
            #This is only triggered if Cycle Mode was activated, so return to Neutral
            print("[SM] Cycled a grip! Now entering neutral with new default grip of ", str(new_default))
            self.current_mode = modes.Neutral
            self._default_grip = new_default

    @property
    def user_command_detected(self):
        return self._user_command_detected

    @user_command_detected.setter
    def user_command_detected(self, new_command):
        #If this user input (either True for some input, or False if no input) is different from the last frame
        if new_command != self.user_command_detected:
            #Save this new pulse as the current user input
            self._user_input_time = time.time()
        self._user_command_detected = new_command

    @property 
    def is_unique_input(self):
        return self._user_input_time != self._previous_user_input_time

    #Use this to mark a user input as processed
    def input_processed_successfully(self):
        self._previous_user_input_time = self._user_input_time

    @property
    def user_input_time(self):
        return self._user_input_time

    @property
    def run_time(self):
        self._run_time = time.time() - self._program_T0
        return self._run_time

    #The timestamp at which this mode was entered
    @property 
    def mode_time(self):
        return self._mode_time

    def set_mode_time(self):
        self._mode_time = time.time()
        print("[SM-MODE TIMER] Updating mode time to ", str(self._mode_time))

    def mode_time_passed(self, delta_req):
        return (time.time() - self.user_input_time) > delta_req

    ########## Active Management

    def activate_gcm(self):
        #If checks are passed, enter into grip control mode to signal the system it needs to be processing
        #   user input into continuous servo commands

        #Set the current mode to GCM
        print("[GCM-DEBUG] Testing to see if GCM should be entered: ")
        if self.user_input_time >= timers.time_required_for_user_command.value and self.is_unique_input:
            self.current_mode = modes.GCM
            print("\t[GCM-DEBUG] Test passed! Entering GCM mode.")
            return True
        return False

    # def switch_grips(self):
    #     #If checks are passed, enter into cycle grip mode to signal the system it needs to change grips

    #     #If in neutral mode, enter cycle grip mode
    #     if self.current_mode == modes.Neutral and self.mode_time_passed(timers.time_required_for_user_command.value) and self.is_unique_input:
    #         self.current_mode = modes.Cycle_Grip
    #         return True
    #     return False

    # def switch_modes(self):
    #     #If checks are passed, enter either into GCM, AGS, or Neutral

    #     #if in AGS or Neutral, toggle top mode
    #     print("[SWITCH MODES] mode time passed? ", str(self.mode_time_passed(timers.time_required_for_any_state.value)))
    #     print("[SWITCH MODES] Unique input? ", str(self.is_unique_input))
    #     if self.mode_time_passed(timers.time_required_for_any_state.value) and self.is_unique_input:
    #         if (self.current_mode == modes.Neutral) or (self.current_mode == modes.AGS):
    #             self.toggle_top_mode()
    #             print("[SWITCH MODES] Called toggle top mode ")
    #             return True
    #         elif (self.current_mode == modes.GCM):
    #             #Else if in GCM, return to top mode
    #             self.current_mode = self.top_mode
    #             print("[SWITCH MODES] Left GCM")
    #             return True
    #     return False

    def no_input_manager(self):
        #If checks are passed, make the current mode the top mode

        #If currently in GCM and timer has passed
        if self.current_mode == modes.GCM and self.mode_time_passed(timers.no_input_return_time.value):
            self.current_mode = self.top_mode
            return True
        return False

    def master_state_tracker(self, user_input):
        """
        Used for the main control algorithm in the program.

        Inputs:
            The current type of user input, from the hand_classes constants
        """
        # print("[SM-DEBUG] Received state of ", str(user_input))
        if user_input is not input_types.none:
            self.user_command_detected = True
        else:
            self.user_command_detected = False
        input_processed = self.inputs_to_events_mapping[user_input]()
        if input_processed:
            self.input_processed_successfully()