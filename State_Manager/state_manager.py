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

from enum import Enum

class modes(Enum):
    Neutral = 1  #Default grip selection, AGS off  (Top mode)
    AGS = 2      #Automated Grip Selection         (Top mode)
    GCM = 3      #Grip Control Mode        
    Trainer = 4  #Training mode for user customizations

#These are triggering events that may or may not cause a change in mode, or lead to another event
class events(Enum):
    invalid = 0
    hold_squeeze_down = 1
    pulse_squeeze_down = 2
    squeeze_up = 3
    top_mode_change = 4   

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
            events.invalid: events.invalid,
            events.hold_squeeze_down: modes.GCM,
            events.pulse_squeeze_down: events.pulse_squeeze_down,
            events.squeeze_up: events.top_mode_change
        }

        #Maps how system inputs map to events
        self.inputs_to_events_mapping = {
            (): True,
            [1]: False
        }
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
        self._current_mode = new_mode

    #Simply toggles what the current top mode is
    def toggle_stop_mode(self):
        self._top_mode = self.top_modes[self._top_mode]

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
        return self._user_command_detected

    def master_state_tracker(self, down_input, up_input):
        """
        Used for the main control algorithm in the program.

        Inputs:
            reported_object: Whether or not the system has an object being reported. 
            down_input:      Whether or not a user command has been detected on the down channel.
            up_input:        Whether or not a user command has been detected on the up channel.
        """
        #Generate the master input mapper, which is a list 
        Input_Mapper = [
            
        ]
    
