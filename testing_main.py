import time
import os
import threading

from Muscle_Driver import muscle

mi = muscle.muscle_interface()

while True:
    if mi.peakTriggered():
        print("triggered")