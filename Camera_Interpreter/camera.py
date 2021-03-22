from enum import Enum

class states(Enum):
    state_1 = 1
    state_2 = 2


class camera_interface():

    def __init__(self):
        my_var = 2

    def get_my_var(self):
        return states.state_1