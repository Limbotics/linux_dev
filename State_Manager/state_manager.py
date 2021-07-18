""" This package provides the interface for the system to change the status lights."""
from typing import Sequence
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

from enum import Enum

class modes(Enum):
    Neutral = 1  #Default grip selection, AGS off  (Top mode)
    AGS = 2      #Automated Grip Selection         (Top mode)
    GCM = 3      #Grip Control Mode        
    Trainer = 4  #Training mode for user customizations
    Cycle_Grip = 5 

#These are triggering events that may or may not cause a change in mode, or lead to another event
class events(Enum):
    activate_ags = 1
    switch_grips = 2
    switch_modes = 3
    switch_top_mode = 4   

class Mode_Manager():
    _program_T0 = time.time()
    _reported_object = ""
    _user_command_detected = False
    _mode_time = time.time() - _program_T0
    _run_time = time.time() - _program_T0
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
        self._top_mode = modes.Neutral

        #Maps how events link to modes and other events
        self.event_mapping = {
            events.activate_ags: modes.AGS,
            events.switch_grips: events.switch_grips,
            events.switch_modes: events.switch_modes
        }

        #Maps how system inputs map to events
        self.inputs_to_events_mapping = {
            input_types.up_input: self.switch_modes, #Up inputs switch the mode, always
            input_types.down_pulse: self.switch_grips, #Down pulses cycle grip selection in neutral mode
            input_types.down_hold: self.activate_gcm,  #Down holding always activates GCM
            input_types.no_input: self.no_input_manager #No input causes events after timers
        }
        pass

    @property
    def info(self):
        # Build a human-readable format of the current system state
        pass
    
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

    #Toggles the top mode, additionally, the top mode MUSt change with the current mode.
    def toggle_top_mode(self):
        self._top_mode = self.top_modes[self._top_mode]
        self.current_mode = self._top_mode

    ######### Param management
    @property
    def reported_object(self):
        return self._reported_object

    @reported_object.setter
    def reported_object(self, new_object):
        self._reported_object = new_object

    @property
    def user_command_detected(self):
        return self._user_command_detected

    @user_command_detected.setter
    def user_command_detected(self, new_command):
        self._user_command_detected = new_command

    @property
    def run_time(self):
        self._run_time = time.time() - self._program_T0
        return self._run_time

    @property 
    def mode_time(self):
        return self._mode_time

    def set_mode_time(self):
        self._mode_time = time.time() - self._mode_time

    ########## Active Management

    def activate_gcm(self):
        #If checks are passed, enter into grip control mode to signal the system it needs to be processing
        #   user input into continuous servo commands

        #Set the current mode to GCM
        pass

    def grip_switch_completed(self):
        #Public function used for the system to signal to the state manager that the grip cycle was completed
        
        #Set the current mode to top mode
        pass

    def switch_grips(self):
        #If checks are passed, enter into cycle grip mode to signal the system it needs to change grips

        #If in neutral mode, enter cycle grip mode
        pass

    def switch_modes(self):
        #If checks are passed, enter either into GCM, AGS, or Neutral

        #if in AGS or Neutral, toggle top mode

        #Else if in GCM, return to top mode
        pass

    def no_input_manager(self):
        #If checks are passed, make the current mode the top mode

        #If currently in GCM and timer has passed
        if self.current_mode == modes.GCM and self.mode_time >= timers.no_input_return_time.value:
            
        pass

    def master_state_tracker(self, user_input):
        """
        Used for the main control algorithm in the program.

        Inputs:
            The current type of user input, from the hand_classes constants
        """
        if user_input is not input_types.no_input:
            self.user_command_detected = True
        else:
            self.user_command_detected = False
        self.inputs_to_events_mapping[user_input]