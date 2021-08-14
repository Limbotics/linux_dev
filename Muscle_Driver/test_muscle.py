import queue
import time
import tempmusclelib.ADS1x15 as ADS1x15
import tempmusclelib.ADS1015 as ADS1015
import Adafruit_GPIO.I2C as I2C


prei2c = I2C
_device = prei2c.get_i2c_device(0x48, busnum=2)
preads = ADS1x15(prei2c)
ads = ADS1015(preads)
#ads.mode = Mode.CONTINUOUS                 #set to continous to speed up reads
#ads.gain = 16                              #adjust gain using this value (does not affect voltage parameter)
_ = ads._data_rate_config(self, 128)
_ = ads._conversion_value(self, -5000, 5000)

#line to read the value of the channel
value = ads.read_adc(self, 0, gain=1)

print(value)