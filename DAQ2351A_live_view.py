import pyvisa
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from functools import partial

class KeysightDAC:
    def __init__(self, usb_address):
        self.usb_address = usb_address
        self.resource_manager = pyvisa.ResourceManager()
        self.instrument = None

    def connect(self):
        self.instrument = self.resource_manager.open_resource(self.usb_address)
        print(f"Connected to: {self.instrument.query('*IDN?')}")

    def send_command(self, command):
        self.instrument.write(command)

    def query(self, command):
        return self.instrument.query(command)
    
    def read_raw(self):
        return self.instrument.read_raw()

    def query_binary_values(self, command):
        return self.instrument.query_binary_values(command, datatype='c', is_big_endian=False, header_fmt='ieee')
    
    def configure_output(self, channel, voltage):
        self.send_command(f'SOURce{channel}:VOLTage {voltage}')

    def measure_output(self, channel):
        return float(self.query(f'MEAS? (@{channel})'))

    def define_sampling_rate(self, rate):
        self.send_command("ACQuire:SRATe {}".format(rate))  # rate shall be in Hertz
        
    def define_sample_points(self, number_of_points):
        self.send_command("WAV:POIN {}".format(number_of_points))

    def close(self):
        if self.instrument:
            self.instrument.close()
            
    def convert_raw_values(self, raw_values, scale):
        byte_nbr = int(raw_values[2:10].decode())  # Get the number of bytes
        index = 10  # Start the index at 10
        decimal_values = []  # Initialize an empty list to store the decimal values
        
        while index < 10 + byte_nbr:
            # Combine the two bytes, reversing their order
            combined_value = (raw_values[index + 1] << 8) | raw_values[index]
            
            # Check the sign bit (most significant bit)
            if combined_value & 0x8000 == 0:
                # Positive value
                decimal_value = ((combined_value / 65536) + 0.5) * scale
            else:
                # Negative value, use only the lower 15 bits
                decimal_value = ((combined_value & 0x7FFF) / 65536) * scale
                
            decimal_values.append(decimal_value)  # Store the decimal value in the list
            
            index += 2
            
        return np.array(decimal_values)  # Convert the list to a NumPy array and return it

# Définition de y_data en dehors de la classe pour la rendre globale
y_data = []

def update_plot(frame, dac):
    global y_data
    dac.connect()
    status = dac.query('WAV:STAT?')
    while "DATA" not in status:
        status = dac.query('WAV:STAT?')
    
    dac.send_command('WAV:DATA?')
    result = dac.read_raw()
    values = dac.convert_raw_values(result, scale)
    y_data.extend(values)
    if len(y_data) > 200000:
        y_data = y_data[-200000:]

    line.set_data(range(len(y_data)), y_data)
    ax.relim()
    ax.autoscale_view()
    dac.close()
    return line,

if __name__ == "__main__":
    usb_address = "USB0::0x0957::0x0F18::TW50200512::0::INSTR"  # Replace with your actual USB address
    dac = KeysightDAC(usb_address)

    try:
        dac.connect()
        print(dac.measure_output(101))
        dac.define_sampling_rate(250000)  # 250Ks/s
        dac.define_sample_points(100000)
        
        time.sleep(0.5)
        dac.send_command('ROUT:CHAN:POL UNIP,(@101)')
        print(dac.query('ROUT:CHAN:POL? (@101)'))
        time.sleep(0.5)
        dac.send_command('ROUT:CHAN:RANG 10,(@101)')  # define voltage range @+/-5V
        scale = int(dac.query('ROUT:CHAN:RANG? (@101)'))
        print(scale)
        time.sleep(0.5)
        dac.send_command('RUN')
        status = dac.query('WAV:STAT?')
        
        while "DATA" not in status:
            status = dac.query('WAV:STAT?')
            
        fig, ax = plt.subplots()
        line, = ax.plot([], [], lw=2)
        ax.grid()

        ani = FuncAnimation(fig, partial(update_plot, dac=dac), blit=True, interval=100)
        
        plt.show()

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        dac.send_command('STOP')
        dac.close()
