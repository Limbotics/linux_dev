from enum import Enum, auto
from typing import ChainMap

import queue
import time
import rpyc #Muscle sensor debugging
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import numpy as np

from Hand_Classes import hand_interface
input_types = hand_interface.input_types

import Adafruit_GPIO.I2C as I2C

#https://www.instructables.com/MuscleCom-Muscle-Controlled-Interface/
#https://learn.adafruit.com/adafruit-4-channel-adc-breakouts/python-circuitpython
#for blinka requirement:
#https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-


# Register and other configuration values:
ADS1x15_DEFAULT_ADDRESS        = 0x48
ADS1x15_POINTER_CONVERSION     = 0x00
ADS1x15_POINTER_CONFIG         = 0x01
ADS1x15_POINTER_LOW_THRESHOLD  = 0x02
ADS1x15_POINTER_HIGH_THRESHOLD = 0x03
ADS1x15_CONFIG_OS_SINGLE       = 0x8000
ADS1x15_CONFIG_MUX_OFFSET      = 12
# Maping of gain values to config register values.
ADS1x15_CONFIG_GAIN = {
    2/3: 0x0000,
    1:   0x0200,
    2:   0x0400,
    4:   0x0600,
    8:   0x0800,
    16:  0x0A00
}
ADS1x15_CONFIG_MODE_CONTINUOUS  = 0x0000
ADS1x15_CONFIG_MODE_SINGLE      = 0x0100
# Mapping of data/sample rate to config register values for ADS1015 (faster).
ADS1015_CONFIG_DR = {
    128:   0x0000,
    250:   0x0020,
    490:   0x0040,
    920:   0x0060,
    1600:  0x0080,
    2400:  0x00A0,
    3300:  0x00C0
}
# Mapping of data/sample rate to config register values for ADS1115 (slower).
ADS1115_CONFIG_DR = {
    8:    0x0000,
    16:   0x0020,
    32:   0x0040,
    64:   0x0060,
    128:  0x0080,
    250:  0x00A0,
    475:  0x00C0,
    860:  0x00E0
}
ADS1x15_CONFIG_COMP_WINDOW      = 0x0010
ADS1x15_CONFIG_COMP_ACTIVE_HIGH = 0x0008
ADS1x15_CONFIG_COMP_LATCHING    = 0x0004
ADS1x15_CONFIG_COMP_QUE = {
    1: 0x0000,
    2: 0x0001,
    4: 0x0002
}
ADS1x15_CONFIG_COMP_QUE_DISABLE = 0x0003

#Replacement AnalogIn class if we're in debug mode
class Analog_Debug():

    def __init__(self):
        self.value = 0

    #Update the value stored in this class
    def update_value(self, new_value):
        self.value = new_value

    def read_adc(self, num, gain=0):
        return self.value

class muscle_interface():
    """This provides the inputs from the user muscle sensors."""
    #self disconnected is class variable that states whether or not human input is being used
    def __init__(self, disconnect=False):
        if(not disconnect):
            # try:
            
            self.ads = ADS1015(busnum=2)
            _ = self.ads._data_rate_config(128)
            _ = self.ads._conversion_value( 0, 2000)

            #line to read the value of the channel
            self.value = self.ads.read_adc(0, gain=1)

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

            # except Exception as e:
            #     print("[M] Error: ", str(e))
            #     print("[DEBUG] Error loading muscle input; defaulting to debug mode")
            #     disconnect = True
            #     print("[LOADING] Connecting to sensor input simulator...")
            
        if(disconnect):
            #Define all my debug plotting values
            figure(figsize=(16, 12), dpi=80)
            self.program_T0 = time.time()
            self.raw_data_time = []
            self.raw_data = []
            self.filtered_data_time = []
            self.filtered_data = []
            self.ads = Analog_Debug()
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
            self.analogThreshold_0 = 500 
            self.max_input_0 = 1500
            
        self.pmd = 0
        self.grip_T0 = time.time()  #Used for tracking grip inputs over thresholds
        self.input_T0 = time.time() #Used for tracking raw inputs over thresholds
        self.last_input = (input_types.none, 0, time.time()) #The last input pair reported by AnalogRead
        self.temp_input = (input_types.none, 0, time.time()) #The temporary, nonreported input to compare to last_input
        self.averaging_array = []
        self.binary_threshold = 0.85

        #Create the percentage buckets
        #Generate predefined % positions along the grip
        self.perc_buckets = []
        counter = 0
        spacing = 10/100 #Always a factor of 100%
        while counter <= 1:
            self.perc_buckets.append(counter)
            counter += spacing

    def update_0_threshold(self):
        self.analogThreshold_0 = self.ads.read_adc(0, gain=1)
        print("[CALIBRATION-CH0] Setting input threshold as ", self.analogThreshold_0)

    def update_0_max(self):
        #Put the input for this channel into an array across 1 second, then take the average
        start = time.time()
        input_array = []
        while (time.time() - start) < 1:
            input_array.append(self.ads.read_adc(0, gain=1))

        #Set val to be average of past second
        self.max_input_0 = sum(input_array)/len(input_array)

        #Set threshold to be half the range
        # self.analogThreshold_0 = (self.max_input_0-self.analogThreshold_0)/2 + self.analogThreshold_0

    def read_filtered(self):
        """
        Read the raw ADS value and return the current filtered value.
        """
        #Constants
        array_avg_len = 20 #The number of readings to average across
        mvg_avg = 20

        #Read the raw value
        raw_val = 0
        if not self.disconnected:
            raw_val = self.ads.read_adc(0, gain=1)
        else:
            raw_val = self.c.root.channel_0_value()

        #Save the raw data to the debug plot
        self.raw_data_time.append(time.time() - self.program_T0)
        self.raw_data.append(raw_val)

        #Check edge case on startup
        self.averaging_array.append(raw_val)
        if len(self.averaging_array) <= mvg_avg:
            # print("[EMG] Returning raw val, since we have no curve.")
            return raw_val
        elif len(self.averaging_array) > array_avg_len:
            # print("[EMG] Popping array element..")
            self.averaging_array.pop(0)

        # print("[EMG] Array: ", str(self.averaging_array))
        t = time.time()
        smoothed = self.smooth(self.averaging_array)
        self.smoothing_time = time.time() - t
        # print("[EMG] Returning smoothed value of ", str(smoothed[-1]))
        return smoothed[-1]

    #Process the inputs past the thresholds 
    #Returns the type of muscle input and the accompanying intensity
    def AnalogRead(self):
        # The fastest rate at which input states can change between down/none
        input_persistency = 0.25
        if self.disconnected:
            new_down_value = self.c.root.channel_0_value() ####

            self.ads.update_value(new_down_value)

        input_value = self.read_filtered()

        #Save the filtered value to the debug plot
        self.filtered_data_time.append(time.time() - self.program_T0)
        self.filtered_data.append(input_value)

        #Convert raw analog into percentage range 
        new_pmd = self.convert_perc(input_value, input_types.down)

        #Check if we have a difference in what we're reporting and the current state
        if new_pmd and self.last_input[0] == input_types.none:
            #We are detecting input from the user, so create the new temp input object to track if not already exists
            if self.temp_input[2] == 0:
                #Save the new temp input object
                self.temp_input = (input_types.down, input_value, time.time())
            elif (self.temp_input[2] - self.last_input[2]) > input_persistency: #Already created, so just compare the timers
                #We're over threshold, so report new input type
                self.last_input = self.temp_input
                self.pmd = new_pmd
                self.temp_input = (input_types.down, input_value, 0)
        elif not new_pmd and self.last_input[0] == input_types.down:
            #We're reporting user input but not receiving it, start timer
            if self.temp_input[2] == 0:
                #Save the new temp input object
                self.temp_input = (input_types.none, input_value, time.time())
            elif (self.temp_input[2] - self.last_input[2]) > input_persistency: #Already created, so just compare the timers
                #We're over threshold, so report new input type
                self.last_input = self.temp_input
                self.pmd = new_pmd
                self.temp_input = (input_types.none, input_value, 0)
        else:
            #reset temp input object 
            self.temp_input = (self.last_input[0], self.last_input[1], 0)
        return self.last_input[0]

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
                new_perc = self.closest(self.perc_buckets, perc)
                if new_perc > self.binary_threshold:
                    return 1
                else:
                    return 0
            else:
                return 0
        else:
            return 0

    def shutdown(self):
        """Save the debug data, if it exists."""
        #Debug
        plt.plot(self.raw_data_time, self.raw_data, label="Raw Data")
        plt.plot(self.filtered_data_time, self.filtered_data, label="Filtered Data")
        plt.legend()
        plt.xlabel("Time")
        plt.ylabel("EMG input")
        plt.savefig('emg_input.png')
        print("[EMG] Saved Debug plot successfully!")
        
    #Given a list of values and another Number, return the closest value within list to the given Number
    def closest(self, list, Number):
        aux = []
        for valor in list:
            aux.append(abs(Number-valor))

        new_val = list[aux.index(min(aux))]
        # print("Changing input from ", str(Number), " to ", str(new_val))
        return new_val

    def smooth(self, data, n=3):
        ret = np.cumsum(data, dtype=float)
        ret[n:] = ret[n:] - ret[:-n]
        return ret[n - 1:] / n

class ADS1x15(object):
    """Base functionality for ADS1x15 analog to digital converters."""

    def __init__(self, address=ADS1x15_DEFAULT_ADDRESS, i2c=None, **kwargs):
        if i2c is None:
            import Adafruit_GPIO.I2C as I2C
            i2c = I2C
        self._device = i2c.get_i2c_device(address, **kwargs)

    def _data_rate_default(self):
        """Retrieve the default data rate for this ADC (in samples per second).
        Should be implemented by subclasses.
        """
        raise NotImplementedError('Subclasses must implement _data_rate_default!')

    def _data_rate_config(self, data_rate):
        """Subclasses should override this function and return a 16-bit value
        that can be OR'ed with the config register to set the specified
        data rate.  If a value of None is specified then a default data_rate
        setting should be returned.  If an invalid or unsupported data_rate is
        provided then an exception should be thrown.
        """
        raise NotImplementedError('Subclass must implement _data_rate_config function!')

    def _conversion_value(self, low, high):
        """Subclasses should override this function that takes the low and high
        byte of a conversion result and returns a signed integer value.
        """
        raise NotImplementedError('Subclass must implement _conversion_value function!')

    def _read(self, mux, gain, data_rate, mode):
        """Perform an ADC read with the provided mux, gain, data_rate, and mode
        values.  Returns the signed integer result of the read.
        """
        config = ADS1x15_CONFIG_OS_SINGLE  # Go out of power-down mode for conversion.
        # Specify mux value.
        config |= (mux & 0x07) << ADS1x15_CONFIG_MUX_OFFSET
        # Validate the passed in gain and then set it in the config.
        if gain not in ADS1x15_CONFIG_GAIN:
            raise ValueError('Gain must be one of: 2/3, 1, 2, 4, 8, 16')
        config |= ADS1x15_CONFIG_GAIN[gain]
        # Set the mode (continuous or single shot).
        config |= mode
        # Get the default data rate if none is specified (default differs between
        # ADS1015 and ADS1115).
        if data_rate is None:
            data_rate = self._data_rate_default()
        # Set the data rate (this is controlled by the subclass as it differs
        # between ADS1015 and ADS1115).
        config |= self._data_rate_config(data_rate)
        config |= ADS1x15_CONFIG_COMP_QUE_DISABLE  # Disble comparator mode.
        # Send the config value to start the ADC conversion.
        # Explicitly break the 16-bit value down to a big endian pair of bytes.
        self._device.writeList(ADS1x15_POINTER_CONFIG, [(config >> 8) & 0xFF, config & 0xFF])
        # Wait for the ADC sample to finish based on the sample rate plus a
        # small offset to be sure (0.1 millisecond).
        time.sleep(1.0/data_rate+0.0001)
        # Retrieve the result.
        result = self._device.readList(ADS1x15_POINTER_CONVERSION, 2)
        return self._conversion_value(result[1], result[0])

    def _read_comparator(self, mux, gain, data_rate, mode, high_threshold,
                         low_threshold, active_low, traditional, latching,
                         num_readings):
        """Perform an ADC read with the provided mux, gain, data_rate, and mode
        values and with the comparator enabled as specified.  Returns the signed
        integer result of the read.
        """
        assert num_readings == 1 or num_readings == 2 or num_readings == 4, 'Num readings must be 1, 2, or 4!'
        # Set high and low threshold register values.
        self._device.writeList(ADS1x15_POINTER_HIGH_THRESHOLD, [(high_threshold >> 8) & 0xFF, high_threshold & 0xFF])
        self._device.writeList(ADS1x15_POINTER_LOW_THRESHOLD, [(low_threshold >> 8) & 0xFF, low_threshold & 0xFF])
        # Now build up the appropriate config register value.
        config = ADS1x15_CONFIG_OS_SINGLE  # Go out of power-down mode for conversion.
        # Specify mux value.
        config |= (mux & 0x07) << ADS1x15_CONFIG_MUX_OFFSET
        # Validate the passed in gain and then set it in the config.
        if gain not in ADS1x15_CONFIG_GAIN:
            raise ValueError('Gain must be one of: 2/3, 1, 2, 4, 8, 16')
        config |= ADS1x15_CONFIG_GAIN[gain]
        # Set the mode (continuous or single shot).
        config |= mode
        # Get the default data rate if none is specified (default differs between
        # ADS1015 and ADS1115).
        if data_rate is None:
            data_rate = self._data_rate_default()
        # Set the data rate (this is controlled by the subclass as it differs
        # between ADS1015 and ADS1115).
        config |= self._data_rate_config(data_rate)
        # Enable window mode if required.
        if not traditional:
            config |= ADS1x15_CONFIG_COMP_WINDOW
        # Enable active high mode if required.
        if not active_low:
            config |= ADS1x15_CONFIG_COMP_ACTIVE_HIGH
        # Enable latching mode if required.
        if latching:
            config |= ADS1x15_CONFIG_COMP_LATCHING
        # Set number of comparator hits before alerting.
        config |= ADS1x15_CONFIG_COMP_QUE[num_readings]
        # Send the config value to start the ADC conversion.
        # Explicitly break the 16-bit value down to a big endian pair of bytes.
        self._device.writeList(ADS1x15_POINTER_CONFIG, [(config >> 8) & 0xFF, config & 0xFF])
        # Wait for the ADC sample to finish based on the sample rate plus a
        # small offset to be sure (0.1 millisecond).
        time.sleep(1.0/data_rate+0.0001)
        # Retrieve the result.
        result = self._device.readList(ADS1x15_POINTER_CONVERSION, 2)
        return self._conversion_value(result[1], result[0])

    def read_adc(self, channel, gain=1, data_rate=None):
        """Read a single ADC channel and return the ADC value as a signed integer
        result.  Channel must be a value within 0-3.
        """
        assert 0 <= channel <= 3, 'Channel must be a value within 0-3!'
        # Perform a single shot read and set the mux value to the channel plus
        # the highest bit (bit 3) set.
        return self._read(channel + 0x04, gain, data_rate, ADS1x15_CONFIG_MODE_SINGLE)

    def read_adc_difference(self, differential, gain=1, data_rate=None):
        """Read the difference between two ADC channels and return the ADC value
        as a signed integer result.  Differential must be one of:
          - 0 = Channel 0 minus channel 1
          - 1 = Channel 0 minus channel 3
          - 2 = Channel 1 minus channel 3
          - 3 = Channel 2 minus channel 3
        """
        assert 0 <= differential <= 3, 'Differential must be a value within 0-3!'
        # Perform a single shot read using the provided differential value
        # as the mux value (which will enable differential mode).
        return self._read(differential, gain, data_rate, ADS1x15_CONFIG_MODE_SINGLE)

    def start_adc(self, channel, gain=1, data_rate=None):
        """Start continuous ADC conversions on the specified channel (0-3). Will
        return an initial conversion result, then call the get_last_result()
        function to read the most recent conversion result. Call stop_adc() to
        stop conversions.
        """
        assert 0 <= channel <= 3, 'Channel must be a value within 0-3!'
        # Start continuous reads and set the mux value to the channel plus
        # the highest bit (bit 3) set.
        return self._read(channel + 0x04, gain, data_rate, ADS1x15_CONFIG_MODE_CONTINUOUS)

    def start_adc_difference(self, differential, gain=1, data_rate=None):
        """Start continuous ADC conversions between two ADC channels. Differential
        must be one of:
          - 0 = Channel 0 minus channel 1
          - 1 = Channel 0 minus channel 3
          - 2 = Channel 1 minus channel 3
          - 3 = Channel 2 minus channel 3
        Will return an initial conversion result, then call the get_last_result()
        function continuously to read the most recent conversion result.  Call
        stop_adc() to stop conversions.
        """
        assert 0 <= differential <= 3, 'Differential must be a value within 0-3!'
        # Perform a single shot read using the provided differential value
        # as the mux value (which will enable differential mode).
        return self._read(differential, gain, data_rate, ADS1x15_CONFIG_MODE_CONTINUOUS)

    def start_adc_comparator(self, channel, high_threshold, low_threshold,
                             gain=1, data_rate=None, active_low=True,
                             traditional=True, latching=False, num_readings=1):
        """Start continuous ADC conversions on the specified channel (0-3) with
        the comparator enabled.  When enabled the comparator to will check if
        the ADC value is within the high_threshold & low_threshold value (both
        should be signed 16-bit integers) and trigger the ALERT pin.  The
        behavior can be controlled by the following parameters:
          - active_low: Boolean that indicates if ALERT is pulled low or high
                        when active/triggered.  Default is true, active low.
          - traditional: Boolean that indicates if the comparator is in traditional
                         mode where it fires when the value is within the threshold,
                         or in window mode where it fires when the value is _outside_
                         the threshold range.  Default is true, traditional mode.
          - latching: Boolean that indicates if the alert should be held until
                      get_last_result() is called to read the value and clear
                      the alert.  Default is false, non-latching.
          - num_readings: The number of readings that match the comparator before
                          triggering the alert.  Can be 1, 2, or 4.  Default is 1.
        Will return an initial conversion result, then call the get_last_result()
        function continuously to read the most recent conversion result.  Call
        stop_adc() to stop conversions.
        """
        assert 0 <= channel <= 3, 'Channel must be a value within 0-3!'
        # Start continuous reads with comparator and set the mux value to the
        # channel plus the highest bit (bit 3) set.
        return self._read_comparator(channel + 0x04, gain, data_rate,
                                     ADS1x15_CONFIG_MODE_CONTINUOUS,
                                     high_threshold, low_threshold, active_low,
                                     traditional, latching, num_readings)

    def start_adc_difference_comparator(self, differential, high_threshold, low_threshold,
                                        gain=1, data_rate=None, active_low=True,
                                        traditional=True, latching=False, num_readings=1):
        """Start continuous ADC conversions between two channels with
        the comparator enabled.  See start_adc_difference for valid differential
        parameter values and their meaning.  When enabled the comparator to will
        check if the ADC value is within the high_threshold & low_threshold value
        (both should be signed 16-bit integers) and trigger the ALERT pin.  The
        behavior can be controlled by the following parameters:
          - active_low: Boolean that indicates if ALERT is pulled low or high
                        when active/triggered.  Default is true, active low.
          - traditional: Boolean that indicates if the comparator is in traditional
                         mode where it fires when the value is within the threshold,
                         or in window mode where it fires when the value is _outside_
                         the threshold range.  Default is true, traditional mode.
          - latching: Boolean that indicates if the alert should be held until
                      get_last_result() is called to read the value and clear
                      the alert.  Default is false, non-latching.
          - num_readings: The number of readings that match the comparator before
                          triggering the alert.  Can be 1, 2, or 4.  Default is 1.
        Will return an initial conversion result, then call the get_last_result()
        function continuously to read the most recent conversion result.  Call
        stop_adc() to stop conversions.
        """
        assert 0 <= differential <= 3, 'Differential must be a value within 0-3!'
        # Start continuous reads with comparator and set the mux value to the
        # channel plus the highest bit (bit 3) set.
        return self._read_comparator(differential, gain, data_rate,
                                     ADS1x15_CONFIG_MODE_CONTINUOUS,
                                     high_threshold, low_threshold, active_low,
                                     traditional, latching, num_readings)

    def stop_adc(self):
        """Stop all continuous ADC conversions (either normal or difference mode).
        """
        # Set the config register to its default value of 0x8583 to stop
        # continuous conversions.
        config = 0x8583
        self._device.writeList(ADS1x15_POINTER_CONFIG, [(config >> 8) & 0xFF, config & 0xFF])

    def get_last_result(self):
        """Read the last conversion result when in continuous conversion mode.
        Will return a signed integer value.
        """
        # Retrieve the conversion register value, convert to a signed int, and
        # return it.
        result = self._device.readList(ADS1x15_POINTER_CONVERSION, 2)
        return self._conversion_value(result[1], result[0])


class ADS1115(ADS1x15):
    """ADS1115 16-bit analog to digital converter instance."""

    def __init__(self, *args, **kwargs):
        super(ADS1115, self).__init__(*args, **kwargs)

    def _data_rate_default(self):
        # Default from datasheet page 16, config register DR bit default.
        return 128

    def _data_rate_config(self, data_rate):
        if data_rate not in ADS1115_CONFIG_DR:
            raise ValueError('Data rate must be one of: 8, 16, 32, 64, 128, 250, 475, 860')
        return ADS1115_CONFIG_DR[data_rate]

    def _conversion_value(self, low, high):
        # Convert to 16-bit signed value.
        value = ((high & 0xFF) << 8) | (low & 0xFF)
        # Check for sign bit and turn into a negative value if set.
        if value & 0x8000 != 0:
            value -= 1 << 16
        return value


class ADS1015(ADS1x15):
    """ADS1015 12-bit analog to digital converter instance."""

    def __init__(self, *args, **kwargs):
        super(ADS1015, self).__init__(*args, **kwargs)

    def _data_rate_default(self):
        # Default from datasheet page 19, config register DR bit default.
        return 1600

    def _data_rate_config(self, data_rate):
        if data_rate not in ADS1015_CONFIG_DR:
            raise ValueError('Data rate must be one of: 128, 250, 490, 920, 1600, 2400, 3300')
        return ADS1015_CONFIG_DR[data_rate]

    def _conversion_value(self, low, high):
        # Convert to 12-bit signed value.
        value = ((high & 0xFF) << 4) | ((low & 0xFF) >> 4)
        # Check for sign bit and turn into a negative value if set.
        if value & 0x800 != 0:
            value -= 1 << 12
        return value