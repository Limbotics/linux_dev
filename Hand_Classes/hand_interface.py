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
    fist = "fist grip"
    pencil = "pencil grip"
    cup = "cup grip"

class grip_finger_angles(Enum):
    """Stores the angle each finger goes to initially for a given grip."""
    openGrip = {
        fingers.thumb:   0,
        fingers.index:   0,
        fingers.middle:  0,
        fingers.ring:    0,
        fingers.pinky:   0
    }

    closeGrip = {
        fingers.thumb:   0,
        fingers.index:   180,
        fingers.middle:  180,
        fingers.ring:    180,
        fingers.pinky:   180
    }

    pencil = {
        fingers.thumb:   150,
        fingers.index:   120,
        fingers.middle:  180,
        fingers.ring:    180,
        fingers.pinky:   180
    }

    cup = {
        fingers.thumb:   140,
        fingers.index:   160,
        fingers.middle:  160,
        fingers.ring:    160,
        fingers.pinky:   160
    }

