from enum import Enum

import board
import busio
import queue
import time

import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn


#https://www.instructables.com/MuscleCom-Muscle-Controlled-Interface/
#https://learn.adafruit.com/adafruit-4-channel-adc-breakouts/python-circuitpython
#for blinka requirement:
#https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi

class muscle_interface():
    """This provides the inputs from the user muscle sensors."""
    #self disconnected is class variable that states whether or not human input is being used
    def __init__(self, disconnect=False):
        if(not disconnect):
            try:
                self.i2c = busio.I2C(board.SCL, board.SDA)  #might need to change to SCL1 SDA1 if i2c channel addresses mess w other channel
                self.ads = ADS.ADS1015(self.i2c)
                #ads.mode = Mode.CONTINUOUS                 #set to continous to speed up reads
                #ads.gain = 16                              #adjust gain using this value (does not affect voltage parameter)
                self.chan = AnalogIn(self.ads, ADS.P0)           #connect pin to A0
                #usage: chan.value, chan.voltage

                self.fifoLength = 10                        #adjust to tune advanced trigger sensitvity
                self.fifo = queue.Queue(self.fifoLength)

                self.analogThreshold = 16000 #17,000 for heath
                self.analogRatioThreshold = 2               #adjust to tune advanced trigger sensitvity
                self.disconnected = False
            except Exception as e:
                print("[DEBUG] Error loading muscle input; defaulting to debug mode")
                disconnect = True
        if(disconnect):
            self.disconnected = True #Flag to not call other things
        self.off_buffer_delay = 1
        self.grip_T0 = time.time()    

    def AnalogRead(self):
        return self.chan.value

    def triggered(self):
        # if self.chan.value > self.analogThreshold:
        #     self.grip_T0 = time.time()
        #     return True
        # elif (time.time() - self.grip_T0 > self.off_buffer_delay):
        #     return False
        try:
            if(not self.disconnected):
                if self.chan.value > self.analogThreshold: # or (time.time() - self.grip_T0 < self.off_buffer_delay)
                    self.grip_T0 = time.time()
                    return True
                elif (time.time() - self.grip_T0 >= self.off_buffer_delay):
                    return False
                if(time.time() - self.grip_T0 < self.off_buffer_delay):
                    return True
        except:
            print("[DEBUG] Muscle sensor reading error - switching to debug mode")
            self.disconnected = True
        
        #Periodic user input sequence
        if(self.disconnected):
            start_loop = 5 #seconds
            end_loop = 6 #seconds
            if(((time.time() - self.grip_T0) >= start_loop) and (time.time() - self.grip_T0 <= end_loop)):
                print("[DEBUG - MS] Sending user input... cutting in T-" + str(end_loop-time.time()+self.grip_T0))
                return True
            elif((time.time() - self.grip_T0) <= start_loop):
                # print("[DEBUG - MS] No user input - T-" + str(start_loop-time.time()+self.grip_T0))
                return False
            else:
                # print("[DEBUG - MS] Resetting user input sequence")
                self.grip_T0 = time.time()
                return False
    
    #hey Jered, this code is meant to be run in a loop. Am I writing this correctly?
    def advancedTriggered(self):
        #create a ghetto fifo buffer and then compare the first and last values. tune the sensitivity by adjusting buffer length
        #turns out theres a fifo module, refernece linked below
        #https://www.guru99.com/python-queue-example.html
        if self.fifo.full():
            previousAnalog = self.fifo.get()            #removes the first value from the FIFO buffer
            currentAnalog = self.chan.value
            self.fifo.put(self.chan.value)              #adds the value from the ADC to the rear of the FIFO buffer

            #it would be cool if we could do a differentiation. (This kind of is because deltaT is unknown)
            if (currentAnalog/previousAnalog) > self.analogRatioThreshold:
                self.grip_T0 = time.time()
                return True
            else:
                if((time.time() - self.grip_T0) > self.off_buffer_delay):
                    return False
                else:
                    return True
        
        self.fifo.put(self.chan.value)                  #adds the value from the ADC to the rear of the FIFO buffer
        
        return False


    