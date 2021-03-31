
import machine
from machine import Pin
#import queue
import utime



class muscle_interface():
    """This provides the inputs from the user muscle sensors."""
    def __init__(self):
        self.chan = machine.ADC(0)                 #GPIO26 chan0

        self.fifoLength = 10                        #adjust to tune advanced trigger sensitvity
        #self.fifo = queue.Queue(self.fifoLength)

        self.conversionFactor = 4095/ (65535)

        self.analogThreshold = 2058
        self.analogRatioThreshold = 3               #adjust to tune advanced trigger sensitvity

    def AnalogRead(self):
        return self.chan.read_u16()*self.conversionFactor

    def triggered(self):
        if self.AnalogRead() > self.analogThreshold:
            print(self.AnalogRead())
            return True
        else:
            print(self.AnalogRead())
            return False

    #hey Jered, this code is meant to be run in a loop. Am I writing this correctly?
"""    def advancedTriggered(self):
        #create a ghetto fifo buffer and then compare the first and last values. tune the sensitivity by adjusting buffer length
        #turns out theres a fifo module, refernece linked below
        #https://www.guru99.com/python-queue-example.html
        if self.fifo.full():
            previousAnalog = self.fifo.get()            #removes the first value from the FIFO buffer
            currentAnalog = self.AnalogRead()
            self.fifo.put(self.AnalogRead())              #adds the value from the ADC to the rear of the FIFO buffer

            #it would be cool if we could do a differentiation. (This kind of is because deltaT is unknown)
            if (currentAnalog/previousAnalog) > self.analogRatioThreshold:
                return True
            else:
                return False
        
        self.fifo.put(self.AnalogRead())                  #adds the value from the ADC to the rear of the FIFO buffer
        
        return False"""

led = Pin(25, Pin.OUT)

Muscle = muscle_interface()
while True:
    if Muscle.triggered():
        print("Triggered")
        led.value(1)
        utime.sleep(2)
    led.value(0)
    
    