from enum import Enum

import board
import busio

import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

i2c = busio.I2C(board.SCL, board.SDA)       #might need to change to SCL1 SDA1 if i2c channel addresses mess w other channel
ads = ADS.ADS1015(i2c)
#ads.gain = 16                              #adjust gain using this value (does not affect voltage parameter)

chan = AnalogIn(ads, ADS.P0)                #connect pin to A0
#usage: chan.value, chan.voltage


#https://www.instructables.com/MuscleCom-Muscle-Controlled-Interface/
#https://learn.adafruit.com/adafruit-4-channel-adc-breakouts/python-circuitpython
#for blinka requirement:
#https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi

class muscle_interface():
    """This provides the inputs from the user muscle sensors."""
    def __init__(self):
        pass

    