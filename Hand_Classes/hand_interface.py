from enum import Enum, auto 

class input_types(Enum):
    down_pulse: auto
    down_hold: auto
    up_input: auto
    no_input: auto

class input_constants(Enum):
    pulse_low: 0.25 #The minimum time for user input to be considered a pulse
    pulse_high: 0.5 #The maximum time for user input to be considered a pulse
    no_input_return_time: 2 #The time for the system to go back to top modes when in lower modes after no input
    time_required_for_any_state = 0.25
    time_required_for_user_command = 0.1

class fingers(Enum):
    """ Defines which servo corresponds to which finger. """
    thumb = 1
    index = 0
    middle = 3
    ring = 2
    pinky = 4

class grips(Enum):
    """ Defines the different grips available."""
    openGrip = "open grip"
    small =    "eventually sciss"
    bottle =   "banana"
    bowl =     "bowl grip"
    test = "test"
    cell = "cell phone"


class grip_finger_angles(Enum):
    """Stores the angle each finger goes to initially for a given grip."""
    openGrip = {
        fingers.thumb.value:   0,
        fingers.index.value:   0,
        fingers.middle.value:  0,
        fingers.ring.value:    0,
        # fingers.pinky.value:   0
    }

    bowl = {
        # fingers.thumb.value:   45,
        # fingers.index.value:   180,
        # fingers.middle.value:  180,
        # fingers.ring.value:    180,
        # fingers.pinky.value:   180
    }

    small = {
        fingers.thumb.value:   45,
        fingers.index.value:   45,
        fingers.middle.value:  180,
        fingers.ring.value:    180,
        # fingers.pinky.value:   180
    }

    small_full_closed = {
        fingers.thumb.value:   180,
        fingers.index.value:   180,
        fingers.middle.value:  180,
        fingers.ring.value:    180,
        # fingers.pinky.value:   180
    }

    bottle = { 
        fingers.thumb.value:   20,
        fingers.index.value:   20,
        fingers.middle.value:  30,
        fingers.ring.value:    30,
    #     fingers.pinky.value:   160
    }

    bottle_full_closed = {
        fingers.thumb.value:   130,
        fingers.index.value:   130,
        fingers.middle.value:  170,
        fingers.ring.value:    170,
    #     fingers.pinky.value:   160
    }

    cell_phone = {
        fingers.thumb.value:   45,
        fingers.index.value:   0,
        fingers.middle.value:  0,
        fingers.ring.value:    100,
    #     fingers.pinky.value:   160
    }

    cell_phone_closed = {
        fingers.thumb.value:   150,
        fingers.index.value:   0,
        fingers.middle.value:  0,
        fingers.ring.value:    180,
    #     fingers.pinky.value:   160
    }

    test = {
        fingers.thumb.value:   180,
        fingers.index.value:   180,
        fingers.middle.value:  180,
        fingers.ring.value:    180,
    #     fingers.pinky.value:   160
    }

