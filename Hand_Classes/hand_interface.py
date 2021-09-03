from enum import Enum, auto 

class input_types(Enum):
    down = 1
    none  = 4

class modes(Enum):
    Neutral = 1  #Default grip selection, AGS off  (Top mode)
    AGS = 2      #Automated Grip Selection         (Top mode)
    GCM = 3      #Grip Control Mode        
    Trainer = 4  #Training mode for user customizations
    Cycle_Grip = 5 

class input_constants(Enum):
    pulse_low = 0.1 #The minimum time for user input to be considered a pulse
    pulse_high = 0.5 #The maximum time for user input to be considered a pulse before it becomes a hold
    no_input_return_time = 1 #The time for the system to go back to top modes when in lower modes after no input
    time_required_for_any_state = 0.25
    time_required_for_user_command = 0.1

class fingers(Enum):
    """ Defines which servo corresponds to which finger. """
    thumb = 0
    index = 1 #0
    middle = 2
    ring = 3
    pinky = 4 #4

# class grip_finger_angles(Enum):
#     """Stores the angle each finger goes to initially for a given grip."""
#     lateral_power = {
#         fingers.thumb.value:   0,
#         fingers.index.value:   0,
#         fingers.middle.value:  15,
#         fingers.ring.value:    15,
#         # fingers.pinky.value:   0
#     }

#     tripod_pinch = {
#         fingers.thumb.value:   45,
#         fingers.index.value:   45,
#         fingers.middle.value:  180,
#         fingers.ring.value:    180,
#         # fingers.pinky.value:   0
#     }

#     thumb_pinch = {
#         fingers.thumb.value:   45,
#         fingers.index.value:   180,
#         fingers.middle.value:  180,
#         fingers.ring.value:    180,
#         # fingers.pinky.value:   180
#     }

#     point = {
#         fingers.thumb.value:   45,
#         fingers.index.value:   45,
#         fingers.middle.value:  180,
#         fingers.ring.value:    180,
#         # fingers.pinky.value:   180
#     }

class grip_names(Enum):
    """Defines the different grip types"""
    lateral_power = "lateral_power"
    tripod = "tripod"
    thumb_pinch = "thumb_pinch"
    point = "point"
    open_palm = "open_palm"

class grip_angles(Enum):
    lateral_power = {
        fingers.thumb.value:   180,
        fingers.index.value:   180,
        fingers.middle.value:  180,
        fingers.ring.value:    180,
        # fingers.pinky.value:   0
    }
    tripod = {
        fingers.thumb.value:   45,
        fingers.index.value:   180,
        fingers.middle.value:  180,
        fingers.ring.value:    180,
        # fingers.pinky.value:   0
    }
    thumb_pinch = {
        fingers.thumb.value:   180,
        fingers.index.value:   75,
        fingers.middle.value:  75,
        fingers.ring.value:    120,
        # fingers.pinky.value:   0
    }
    point = {
        fingers.thumb.value:   180,
        fingers.index.value:   0,
        fingers.middle.value:  180,
        fingers.ring.value:    180,
        # fingers.pinky.value:   180
    }
    open_palm = {
        fingers.thumb.value:   45,
        fingers.index.value:   45,
        fingers.middle.value:  45,
        fingers.ring.value:    45,
        # fingers.pinky.value:   180
    }
    angle_names = {
        grip_names.lateral_power: lateral_power,
        grip_names.tripod: tripod,
        grip_names.thumb_pinch: thumb_pinch,
        grip_names.point: point,
        grip_names.open_palm: open_palm
    }

class grips(Enum):
    """ Defines the different grips available with a dictionary. Maps all objects to different grip angle names."""
    object_to_grip_mapping = {
        "":             grip_angles.lateral_power.value,
        # "umbrella":     grip_angles.lateral_power.value,
        # "handbag" :     grip_angles.lateral_power.value,
        # "tie":          grip_angles.thumb_pinch.value,
        # "suitcase":     grip_angles.thumb_pinch.value,
        # "frisbee":      grip_angles.thumb_pinch.value,
        # "umbrella":     grip_angles.lateral_power.value,
        # "handbag" :     grip_angles.lateral_power.value,
        # "tie":          grip_angles.thumb_pinch.value,
        # "suitcase":     grip_angles.thumb_pinch.value,
        # "frisbee":      grip_angles.thumb_pinch.value,
        "cup":          grip_angles.lateral_power.value,
        "fork":         grip_angles.tripod.value,
        "knife":        grip_angles.tripod.value,
        "spoon":        grip_angles.tripod.value,
        # "bowl":         grip_angles.point.value,
        "banana":       grip_angles.lateral_power.value,
        "apple":        grip_angles.lateral_power.value,
        # "sandwich":     grip_angles.lateral_power.value,
        # "remote":       grip_angles.lateral_power.value,
        "cell phone":   grip_angles.thumb_pinch.value,
        "cell":   grip_angles.thumb_pinch.value,
        "refrigerator": grip_angles.lateral_power.value,
        "keyboard": grip_angles.point.value
        # "cat": grip_angles
        # "microwave":    grip_angles.lateral_power.value,
        # "refrigerator": grip_angles.lateral_power.value,
        # "book":         grip_angles.thumb_pinch.value,
        # "scissors":     grip_angles.lateral_power.value,
        # "toothbrush":   grip_names.tripod.value,
    }
    
    # def next(self):
    #     cls = self.__class__
    #     members = list(cls)
    #     index = members.index(self) + 1
    #     if index >= len(members):
    #         # to cycle around
    #         index = 0
    #     return members[index]