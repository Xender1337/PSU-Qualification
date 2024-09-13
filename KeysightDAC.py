import pyvisa
import numpy as np

class KeysightDAC:
    ANALOG_CHANNEL_1 = 101
    ANALOG_CHANNEL_2 = 102
    ANALOG_CHANNEL_3 = 103
    ANALOG_CHANNEL_4 = 104
    ANALOG_CHANNEL_5 = 105
    ANALOG_CHANNEL_6 = 106
    ANALOG_CHANNEL_7 = 107
    ANALOG_CHANNEL_8 = 108
    ANALOG_CHANNEL_9 = 109
    ANALOG_CHANNEL_10 = 110
    ANALOG_CHANNEL_11 = 111
    ANALOG_CHANNEL_12 = 112
    ANALOG_CHANNEL_13 = 113
    ANALOG_CHANNEL_14 = 114
    ANALOG_CHANNEL_15 = 115
    ANALOG_CHANNEL_16 = 116
    
    VOLTAGE_RANGE_10V = 10
    VOLTAGE_RANGE_5V = 5
    VOLTAGE_RANGE_2V5 = 2.5
    VOLTAGE_RANGE_1V25 = 1.25
    
    CHANNEL_UNIPOLAR_MODE = 'UNIP'
    CHANNEL_BIPOLAR_MODE = 'BIP'
    
    def __init__(self, usb_address):
        self.usb_address = usb_address
        self.resource_manager = pyvisa.ResourceManager()
        self.instrument = None
        self.scanlist = None

    def connect(self):
        self.instrument = self.resource_manager.open_resource(self.usb_address)

    def send_command(self, command):
        print(command)
        self.instrument.write(command)

    def query(self, command):
        return self.instrument.query(command)
    
    def read_raw(self):
        return self.instrument.read_raw()

    def configure_output(self, channel, voltage_range, polarity):
        self.send_command(f'ROUT:CHAN:RANG {voltage_range}, (@{channel})')
        self.send_command(f'ROUT:CHAN:POL {polarity}, (@{channel})')
        
    def get_voltage_range(self, channel):
        return int(self.query(f"ROUT:CHAN:RANG? (@{channel})"))
        
    def configure_scanlist(self, channels):
        self.scanlist = list()
        command = 'ROUT:SCAN (@'
        
        if isinstance(channels, int):
            command += f'{channels})'
        else:
            for a_channel in channels:
                command += f'{a_channel},'
                self.scanlist.append(a_channel)
            command = command[:-1] + ')'
            
        self.send_command(command)

    def measure_output(self, channel):
        return float(self.query(f'MEAS? (@{channel})'))

    def get_sampling_rate(self):
        return float(self.query("ACQuire:SRATe?"))

    def define_sampling_rate(self, rate):
        self.send_command(f"ACQuire:SRATe {rate}") # rate shall be in Hertz
        
    def get_sampling_points(self):
        return self.query("WAV:POIN?")
    
    def define_sample_points(self, number_of_points):
        self.send_command(f"WAV:POIN {number_of_points}")
        target = self.get_sampling_points()
        
        if int(target) != number_of_points:
            print("Can't define the wanted number of points")

    def close(self):
        if self.instrument:
            self.instrument.close()
            
    def start_acquisition(self):
        self.send_command('RUN')
        
    def stop_acquisition(self):
        self.send_command('STOP')
            
    def convert_raw_values(self, raw_values, scale):
        byte_nbr = int(raw_values[2:10].decode())  # Get the number of bytes
        index = 10  # Start the index at 10
        channel_nbr = len(self.scanlist)

        if channel_nbr == 1:
            decimal_values = []
            while index + 1 < 10 + byte_nbr:
                combined_value = (raw_values[index + 1] << 8) | raw_values[index]
                if combined_value & 0x8000 == 0:
                    decimal_value = ((combined_value / 65536) + 0.5) * scale
                else:
                    decimal_value = ((combined_value & 0x7FFF) / 65536) * scale
                decimal_values.append(decimal_value)
                index += 2
            return np.array(decimal_values)
        
        else:
            decimal_values = [[] for _ in range(channel_nbr)]
            channel_index = 0
            while index + 1 < 10 + byte_nbr:
                combined_value = (raw_values[index + 1] << 8) | raw_values[index]
                if combined_value & 0x8000 == 0:
                    decimal_value = ((combined_value / 65536) + 0.5) * scale
                else:
                    decimal_value = ((combined_value & 0x7FFF) / 65536) * scale
                decimal_values[channel_index].append(decimal_value)
                channel_index = (channel_index + 1) % channel_nbr
                index += 2
            return [np.array(vals) for vals in decimal_values]