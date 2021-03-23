from enum import Enum 

class fingers(Enum):
    """ This class defines which servo corresponds to which finger. """
    thumb = 0
    index = 1
    middle = 2
    ring = 3
    pinky = 4

class grips(Enum):
    """ This class defines the different grips available."""
    openGrip = "open"
    fist = "fist"
    pencil = "pencil"
    cup = "cup grip"

