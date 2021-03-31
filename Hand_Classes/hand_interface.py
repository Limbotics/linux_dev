from enum import Enum 

class fingers(Enum):
    """ Defines which servo corresponds to which finger. """
    thumb = 0
    index = 1
    middle = 2
    ring = 3
    pinky = 4

class grips(Enum):
    """ Defines the different grips available."""
    openGrip = "open grip"
    small = "small grip"
    bottle = "cup grip"
    bowl = "bowl grip"


class grip_finger_angles(Enum):
    """Stores the angle each finger goes to initially for a given grip."""
    openGrip = {
        fingers.thumb.value:   0,
        fingers.index.value:   0,
        # fingers.middle.value:  0,
        # fingers.ring.value:    0,
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
        # fingers.thumb.value:   45,
        # fingers.index.value:   120,
        # fingers.middle.value:  180,
        # fingers.ring.value:    180,
        # fingers.pinky.value:   180
    }

    bottle = { 
        fingers.thumb.value:   90,
        fingers.index.value:   90,
        # fingers.middle.value:  180,
    #     fingers.ring.value:    160,
    #     fingers.pinky.value:   160
    }

    bottle_full_closed = {
        fingers.thumb.value:   180,
        fingers.index.value:   180,
        # fingers.middle.value:  180,
    #     fingers.ring.value:    160,
    #     fingers.pinky.value:   160
    }

