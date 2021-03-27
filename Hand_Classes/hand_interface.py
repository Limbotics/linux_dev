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
        fingers.thumb.value:   0,
        # fingers.index.value:   0,
        # fingers.middle.value:  0,
        # fingers.ring.value:    0,
        # fingers.pinky.value:   0
    }

    closeGrip = {
        fingers.thumb.value:   45,
        # fingers.index.value:   180,
        # fingers.middle.value:  180,
        # fingers.ring.value:    180,
        # fingers.pinky.value:   180
    }

    pencil = {
        fingers.thumb.value:   45,
        # fingers.index.value:   120,
        # fingers.middle.value:  180,
        # fingers.ring.value:    180,
        # fingers.pinky.value:   180
    }

    cup = {
        fingers.thumb.value:   45,
        # fingers.index.value:   45,
    #     fingers.middle.value:  160,
    #     fingers.ring.value:    160,
    #     fingers.pinky.value:   160
    # }

