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
                #Test some stuff
                print("SCL: " + str(board.SCL))
                print("SDA: " + str(board.SDA))
                self.i2c = busio.I2C(board.SCL, board.SDA)  #might need to change to SCL1 SDA1 if i2c channel addresses mess w other channel
                self.ads = ADS.ADS1015(self.i2c)
                #ads.mode = Mode.CONTINUOUS                 #set to continous to speed up reads
                #ads.gain = 16                              #adjust gain using this value (does not affect voltage parameter)
                self.chan = AnalogIn(self.ads, ADS.P0)           #connect pin to A0
                #usage: chan.value, chan.voltage

                #for advanced trigger
                self.fifoLength = 10                        #adjust to tune advanced trigger sensitvity
                self.fifo = queue.Queue(self.fifoLength)

                self.analogThreshold = 9000 #17,000 for heath
                self.analogRatioThreshold = 2               #adjust to tune advanced trigger sensitvity
                self.disconnected = False
                #end advanced trigger

                #for bufferedTrigger:
                self.currentBufferList = [None]*20               #adjust buffer length here (this is how many samples it captures before comparing - think of it as a time delay)
                self.currentBufferListMean = 0
                self.previousBufferListMean = 10000              #set high to not trigger initially (prob have to set it to 30k, did not test)
                self.gtThreshold = 2000                          #this is the threshold that the next signal must be greater than in order to trigger the myo sensor - balance the sensitivity of the system with noise and user input strength
                #potentially add feature to catch the falling edge too
                #end bufferedTrigger

                

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
    

    def bufferedTrigger(self):
        #If we're in debug mode just pass to the other function that has the implementation
        if(self.disconnected):
            return self.triggered()

        #create buffers, take mean, see if next buffer is greater by a certain value
        for i in range(len(self.currentBufferList)):
            self.currentBufferList[i] = self.AnalogRead()
        self.currentBufferListMean = sum(self.currentBufferList)/len(self.currentBufferList)    #average mean

        if (self.currentBufferListMean-self.previousBufferListMean) > self.gtThreshold:
            self.previousBufferListMean = self.currentBufferListMean
            return True
        else:
            self.previousBufferListMean = self.currentBufferListMean
            return False
        


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


    