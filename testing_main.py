import time
import os
import threading

from Muscle_Driver import muscle

mi = muscle.muscle_interface()

while True:
    if mi.peakTriggered():
        print("triggered!!!!!!!!!")
    # else:
        # print("not triggered")
    # print(mi.bufferList)
    print(mi.peaks[0])