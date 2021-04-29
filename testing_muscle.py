import time
import os
import threading

from Muscle_Driver import muscle
from Hand_Classes import hand_interface

from Servo_Driver import servo

mi = muscle.muscle_interface(disconnect=False)
servos = servo.handServoControl()

while True:
    if mi.bufferedTrigger():
        print("triggered!!!!!!!!!")
        # print(mi.peaks[0])
        servos.moveFinger(0, 180)
    else:
        servos.moveFinger(0, 0)
        # print("not triggered")
    print(mi.currentBufferListMean)