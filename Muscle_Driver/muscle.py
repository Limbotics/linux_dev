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

# #Simple types to pass to change numbers from scalars to of units down or up
# class IT(Enum):
#     down = 0
#     none = 2

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
                
                self.i2c = busio.I2C(board.I2C2_SDA, board.I2C2_SCL)  #might need to change to SCL1 SDA1 if i2c channel addresses mess w other channel
                self.ads = ADS.ADS1015(self.i2c)
                #ads.mode = Mode.CONTINUOUS                 #set to continous to speed up reads
                #ads.gain = 16                              #adjust gain using this value (does not affect voltage parameter)
                self.chan_0 = AnalogIn(self.ads, ADS.P0)           #connect pin to A0
                # self.chan_1 = AnalogIn(self.ads, ADS.P1)

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
                
                #Initialize the threshold vals, let the calibration sequence handle it later
                self.analogThreshold_0 = 0
                self.max_input_0 = 0
                # self.analogThreshold_1 = 0 
                # self.max_input_1 = 0

            except Exception as e:
                print("[M] Error: ", str(e))
                print("[DEBUG] Error loading muscle input; defaulting to debug mode")
                disconnect = True
                print("[LOADING] Connecting to sensor input simulator...")
            
        if(disconnect):
            self.chan_0 = Analog_Debug()
            # self.chan_1 = Analog_Debug()
            self.disconnected = True #Flag to not call other things

            #Initialize the muscle sensor server
            while(True):
                try:
                    self.c = rpyc.connect("localhost", 18812)
                    break
                except Exception as e:
                    print("[M_DEBUG] Pinging server again in 3 seconds...")
                    time.sleep(3)

            #Define debug-compatible threshold values
            self.analogThreshold_0 = 2000 #17,000 for heath
            self.max_input_0 = 15000
            # self.analogThreshold_1 = 9000 
            # self.max_input_1 = 13000
            
        self.grip_T0 = time.time()  #Used for tracking grip inputs over thresholds
        self.input_T0 = time.time() #Used for tracking raw inputs over thresholds
        self.last_input = (input_types.none, 0) #The last input pair reported by AnalogRead

        #Create the percentage buckets
        #Generate predefined % positions along the grip
        self.perc_buckets = []
        counter = 0
        spacing = 2.5/100 #Always a factor of 100%
        while counter <= 1:
            self.perc_buckets.append(counter)
            counter += spacing

        print("Control buckets: ", str(self.perc_buckets))

    def update_0_threshold(self, new_threshold):
        self.analogThreshold_0 = new_threshold

    def update_0_max(self):
        #Put the input for this channel into an array across 1 second, then take the average
        start = time.time()
        input_array = []
        while (time.time() - start) < 1:
            input_array.append(self.chan_0.value)

        #Set val to be average of past second
        self.max_input_0 = sum(input_array)/len(input_array)

    #Process the inputs past the thresholds 
    #Returns the type of muscle input and the accompanying intensity
    def AnalogRead(self):
        # The fastest rate at which input states can change
        input_persistency = 0.05
        if self.disconnected:
            new_down_value = self.c.root.channel_0_value() ####
            # new_up_value = self.c.root.channel_1_value()   ####

            self.chan_0.update_value(new_down_value)
            # self.chan_1.update_value(new_up_value)

        print("[MDEBUG] Channel 0 input: ", str(self.chan_0.value))
        # print("[MDEBUG] Channel 1 input: ", str(self.chan_1.value))

        #Convert raw analog into percentage range 
        self.pmd = self.convert_perc(self.chan_0.value, input_types.down)

        if ((self.chan_0.value > self.analogThreshold_0 and (time.time() - self.input_T0) > input_persistency) or (self.last_input[1] == input_types.down)):
            print("[MDEBUG] Detecting input on channel 0 above analog threshold")
            self.input_T0 = time.time()
            self.last_input = (input_types.down, self.chan_0.value)
            return self.last_input[0]

        if (time.time() - self.input_T0) > input_persistency:
            self.input_T0 = time.time()
            self.last_input = (input_types.none, 0)
            return self.last_input[0]
        return self.last_input[0]

        # except Exception as e:
        #     raise Exception(str(e))

    def convert_perc(self, raw_analog, type):
        #Converts the raw analog value into a predefined percentage from the list below

    
        if type == input_types.down:
            #If higher than the max input from the calibration, then return 100%
            if raw_analog >= self.max_input_0:
                return 1
            #If in above the analog threshold, then convert to the percentage range
            elif raw_analog > self.analogThreshold_0:
                perc = raw_analog*(1/(self.max_input_0-self.analogThreshold_0)) + (self.analogThreshold_0/(self.analogThreshold_0-self.max_input_0))
                #Convert the raw percentage to a filtered percentage
                return self.closest(self.perc_buckets, perc)
            else:
                return 0
        else:
            return 0

    def closest(self, list, Number):
        aux = []
        for valor in list:
            aux.append(abs(Number-valor))

        new_val = list[aux.index(min(aux))]
        print("Changing input from ", str(Number), " to ", str(new_val))
        return new_val