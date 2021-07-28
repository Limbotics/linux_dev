from enum import Enum, auto
from typing import ChainMap

import board
import busio
import queue
import time
import sys,tty,termios
import rpyc #Muscle sensor debugging

from Hand_Classes import hand_interface
input_types = hand_interface.input_types

import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn


#https://www.instructables.com/MuscleCom-Muscle-Controlled-Interface/
#https://learn.adafruit.com/adafruit-4-channel-adc-breakouts/python-circuitpython
#for blinka requirement:
#https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-

#Simple types to pass to change numbers from scalars to of units down or up
class IT(Enum):
    down = 0
    up = 1
    none = 2

#Replacement AnalogIn class if we're in debug mode
class Analog_Debug():

    def __init__(self):
        self.value = 0

    #Update the value stored in this class
    def update_value(self, new_value):
        self.value = new_value

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
                self.chan_0 = AnalogIn(self.ads, ADS.P0)           #connect pin to A0
                self.chan_1 = AnalogIn(self.ads, ADS.P1)

                self.percent_actuated = 0 #Define the conversion from the self.chan value to a range from 0 to full squeeze
                #usage: chan.value, chan.voltage

                #for advanced trigger
                self.fifoLength = 10                        #adjust to tune advanced trigger sensitvity
                self.fifo = queue.Queue(self.fifoLength)

                
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

                #TODO: Initialize connection across rpyc to the input program
                print("[LOADING] Connecting to sensor input simulator...")
            

        if(disconnect):
            self.chan_0 = Analog_Debug()
            self.chan_1 = Analog_Debug()
            self.disconnected = True #Flag to not call other things

            #Initialize the muscle sensor server
            while(True):
                try:
                    self.c = rpyc.connect("localhost", 18812)
                    break
                except Exception as e:
                    print("[M_DEBUG] Pinging server again in 3 seconds...")
                    time.sleep(3)

        self.analogThreshold_0 = 2000 #17,000 for heath
        self.analogThreshold_1 = 9000 

        self.grip_T0 = time.time()  #Used for tracking grip inputs over thresholds
        self.input_T0 = time.time() #Used for tracking raw inputs over thresholds
        self.last_input = (IT.none, 0) #The last input pair reported by AnalogRead

    #Process the inputs past the thresholds 
    #Returns the type of muscle input and the accompanying intensity
    def AnalogRead(self):
        # try: 
        input_persistency = 0.05
        if self.disconnected:
            new_down_value = self.c.root.channel_0_value() ####
            new_up_value = self.c.root.channel_1_value()   ####

            self.chan_0.update_value(new_down_value)
            self.chan_1.update_value(new_up_value)

        print("[MDEBUG] Channel 0 input: ", str(self.chan_0.value))
        print("[MDEBUG] Channel 1 input: ", str(self.chan_1.value))

        if (self.chan_0.value > self.analogThreshold_0):
            print("[MDEBUG] Detecting input on channel 0 above analog threshold")
            self.input_T0 = time.time()
            self.last_input = (IT.down, self.chan_0.value)
            return self.last_input

        if self.chan_1.value > self.analogThreshold_1:
            print("[MDEBUG] Detecting input on channel 1 above analog threshold")
            self.input_T0 = time.time()
            self.last_input = (IT.up, self.chan_1.value)
            return self.last_input

        if (time.time() - self.input_T0) > input_persistency:
            print("[MDEBUG] No input is above either analog threshold")
            self.input_T0 = time.time()
            self.last_input = (IT.none, 0)
            return self.last_input
        return self.last_input

        # except Exception as e:
        #     raise Exception(str(e))

    def convert_perc(self, raw_analog, type):
        # TODO: Write calibration sequence for the range definitions
        no_input_down = 2000
        max_input_down = 15000

        no_input_up = 1000
        max_input_up = 13000

        no_input = 0
        max_input = 0

        if type == IT.down:
            max_input = max_input_down
            no_input = no_input_down
        elif type == IT.up:
            max_input = max_input_up
            no_input = no_input_up
        else:
            return 0

        if raw_analog >= max_input:
            return 1
        elif raw_analog > no_input:
            return raw_analog*(1/(max_input-no_input)) + (no_input/(no_input-max_input))
        else:
            return 0
        
    def triggered(self):
        # TODO: This needs to be converted into pulses of either short (pulse) or long (hold) according to the timer constants
        # TODO: Convert the reported muscle intensity into percentage distances
        #If we're currently detecting input from the user
        in_data = self.AnalogRead()
        print("[MDEBUG] In_data: ", str(in_data))
        self.pmd = self.convert_perc(in_data[1], in_data[0]) #Converts the raw analog value into percent muscle depth
        if (in_data[0] != IT.none) and self.grip_T0 == 0: #Always track down signals
            self.grip_T0 = time.time()
        elif self.grip_T0 == 0:
            return input_types.no_input

        #If over minimum persistency and under the max, with no input, then we know the user supplied a pulse
        if (time.time() - self.grip_T0) < hand_interface.input_constants.pulse_high.value and (time.time() - self.grip_T0) > hand_interface.input_constants.pulse_low.value and in_data[0] == IT.none:
            #We caught a short pulse, return that for the remaining time of this timeslot
            return input_types.down_pulse
        #If over the hold persistency, then return down hold
        elif (time.time() - self.grip_T0) > hand_interface.input_constants.pulse_high.value and in_data[0] == IT.down:
            return input_types.down_hold

        if in_data[0] == IT.up:
            return input_types.up_input
        elif in_data[0] == IT.none:
            self.grip_T0 = 0
            return input_types.no_input
        return input_types.no_input #Edge case where down_hold is under pulse low value

        # if self.AnalogRead() > self.analogThreshold: # or (time.time() - self.grip_T0 < self.off_buffer_delay)
        #     self.grip_T0 = time.time()
        #     return True
        # elif (time.time() - self.grip_T0 >= self.off_buffer_delay):
        #     return False
        # if(time.time() - self.grip_T0 < self.off_buffer_delay):
        #     return True
        
        #Periodic user input sequence
        # if(self.disconnected):
        #     start_loop = 5 #seconds
        #     end_loop = 6 #seconds
        #     if(((time.time() - self.grip_T0) >= start_loop) and (time.time() - self.grip_T0 <= end_loop)):
        #         print("[DEBUG - MS] Sending user input... cutting in T-" + str(end_loop-time.time()+self.grip_T0))
        #         return input_types.down_hold
        #     elif((time.time() - self.grip_T0) <= start_loop):
        #         # print("[DEBUG - MS] No user input - T-" + str(start_loop-time.time()+self.grip_T0))
        #         return input_types.no_input
        #     else:
        #         # print("[DEBUG - MS] Resetting user input sequence")
        #         self.grip_T0 = time.time()
        #         return input_types.no_input

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
            currentAnalog = self.AnalogRead()
            self.fifo.put(self.AnalogRead())              #adds the value from the ADC to the rear of the FIFO buffer

            #it would be cool if we could do a differentiation. (This kind of is because deltaT is unknown)
            if (currentAnalog/previousAnalog) > self.analogRatioThreshold:
                self.grip_T0 = time.time()
                return True
            else:
                if((time.time() - self.grip_T0) > self.off_buffer_delay):
                    return False
                else:
                    return True
        
        self.fifo.put(self.AnalogRead())                  #adds the value from the ADC to the rear of the FIFO buffer
        
        return False