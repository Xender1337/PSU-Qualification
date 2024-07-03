import pyvisa
import bitstring
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

class KeysightDAC:
    ANALOG_CHANNEL_1    = 101
    ANALOG_CHANNEL_2    = 102
    ANALOG_CHANNEL_3    = 103
    ANALOG_CHANNEL_4    = 104
    ANALOG_CHANNEL_5    = 105
    ANALOG_CHANNEL_6    = 106
    ANALOG_CHANNEL_7    = 107
    ANALOG_CHANNEL_8    = 108
    ANALOG_CHANNEL_9    = 109
    ANALOG_CHANNEL_10   = 110
    ANALOG_CHANNEL_11   = 111
    ANALOG_CHANNEL_12   = 112
    ANALOG_CHANNEL_13   = 113
    ANALOG_CHANNEL_14   = 114
    ANALOG_CHANNEL_15   = 115
    ANALOG_CHANNEL_16   = 116
    
    VOLTAGE_RANGE_10V   = 10
    VOLTAGE_RANGE_5V    = 5
    VOLTAGE_RANGE_2V5   = 2.5
    VOLTAGE_RANGE_1V25  = 1.25
    
    CHANNEL_UNIPOLAR_MODE   = 'UNI'
    CHANNEL_BIPOLAR_MODE    = 'BIP'
    
    def __init__(self, usb_address):
        self.usb_address = usb_address
        self.resource_manager = pyvisa.ResourceManager()
        self.instrument = None

    def connect(self):
        self.instrument = self.resource_manager.open_resource(self.usb_address)
        # print(f"Connected to: {self.instrument.query('*IDN?')}")

    def send_command(self, command):
        self.instrument.write(command)

    def query(self, command):
        return self.instrument.query(command)
    
    def read_raw(self):
        return self.instrument.read_raw()

    def configure_output(self, channel, voltage_range, polarity):
        self.send_command(f'ROUT:CHAN:RANG {voltage_range},(@{channel})')
        self.send_command(f'ROUT:CHAN:POL {polarity},(@{channel})')
        
    def configure_scanlist(self, channels):
        command = 'ROUT:SCAN (@'
        print(type(channels))
        
        if type(channels) is int:
            command = command + '{}'.format(channels)
            command = command + ')'
        else:
            for a_channel in channels:
                command = command + '{},'.format(a_channel)
            command = command[:-1] + ')'
        print(command)
        self.send_command(command)

    def measure_output(self, channel):
        return float(self.query(f'MEAS? (@{channel})'))

    def get_sampling_rate(self):
        return self.query("ACQuire:SRATe?")

    def define_sampling_rate(self, rate):
        self.send_command("ACQuire:SRATe {}".format(rate)) # rate shall be in Hertz
        
    def get_sampling_points(self):
        return self.query("WAV:POIN?")
    
    def define_sample_points(self, number_of_points):
        self.send_command("WAV:POIN {}".format(number_of_points))
        target = self.get_sampling_points()
        
        if int(target) != number_of_points:
            print("Can't define the wanted number of points")

    def close(self):
        if self.instrument:
            self.instrument.close()
            
    def convert_raw_values(self, raw_values, scale):
        byte_nbr = int(raw_values[2:10].decode())  # Get the number of bytes
        # print(raw_values)
        index = 10  # Start the index at 10
        decimal_values = [] # Initialize an empty list to store the decimal values
        
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

if __name__ == "__main__":
    usb_address = "USB0::0x0957::0x0F18::TW50200512::0::INSTR"  # Remplacez par l'adresse USB réelle de votre DAC
    dac = KeysightDAC(usb_address)

    try:
        dac.connect()
        print(dac.measure_output(101))
        dac.define_sampling_rate(125000) #  500Ks/s
        dac.define_sample_points(1000000)
        
        scanlist = [dac.ANALOG_CHANNEL_1, dac.ANALOG_CHANNEL_2]
        dac.configure_scanlist(scanlist)
        
        print(dac.get_sampling_points())
        print(dac.get_sampling_rate())
        
        # print(dac.measure_output(101))
        # dac.define_sampling_rate(250) #  500Ks/s
        # dac.define_sample_points(10)
        # dac.send_command('DIG')
        
        time.sleep(0.5)
        dac.configure_output(dac.ANALOG_CHANNEL_1, dac.VOLTAGE_RANGE_5V, dac.CHANNEL_UNIPOLAR_MODE)
        dac.configure_output(dac.ANALOG_CHANNEL_2, dac.VOLTAGE_RANGE_5V, dac.CHANNEL_UNIPOLAR_MODE)
        # dac.send_command('VOLT:RANG 5,(@101)') # define voltage range @+/-5V
        print(dac.query('ROUT:SCAN?'))
        # print(dac.query('ROUT:CHAN:POL? (@101)'))
        time.sleep(0.5)
        # scale = int(dac.query('ROUT:CHAN:RANG? (@101)'))
        # print(scale)
        time.sleep(0.5)
        dac.send_command('RUN')
        status = dac.query('WAV:STAT?')
        
        
        # if "EPTY" in status:
        #     # print("OK Ready to capture")
        #     pass
        # else:
        #     dac.send_command('STOP')


        # while "DATA" not in status:
        #     status = dac.query('WAV:STAT?')
        # # dac.close()
        # dac.send_command('STOP')
        # now = time.time()
        # dac.send_command('WAV:DATA?')
        # result = dac.read_raw()
        # values = dac.convert_raw_values(result, scale)
        # end = time.time() - now
        # print(values)
        
        # print(end)
        try:
            next_frame = time.time()
            status = dac.query('WAV:STAT?')
            while "DATA" not in status:
                status = dac.query('WAV:STAT?')
                
            now = time.time()
            dac.send_command('WAV:DATA?')
            result = dac.read_raw()
            values = dac.convert_raw_values(result, dac.VOLTAGE_RANGE_5V)
            end = time.time() - now
            print(values.size)
            print(time.time() - next_frame)
            print(end)  
            
              # Plot the values
            plt.figure(figsize=(10, 5))
            plt.plot(values, marker='o', linestyle='-')
            plt.title('Decimal Values')
            plt.xlabel('Index')
            plt.ylabel('Value')
            plt.grid(True)
            plt.show()
                
        except KeyboardInterrupt:
            dac.send_command('STOP')
            dac.close()
            
        #   # Real-time plotting setup
        # fig, ax = plt.subplots(figsize=(10, 5))
        # ax.set_title('Decimal Values in Real-Time')
        # ax.set_xlabel('Index')
        # ax.set_ylabel('Value')
        # line, = ax.plot([], [], marker='o', linestyle='-')
        # ax.grid(True)
        
        # decimal_values = []

        # def update(frame):
        #     now = time.time()
        #     dac.connect()
        #     status = dac.query('WAV:STAT?')
            
        #     while "DATA" not in status:
        #         status = dac.query('WAV:STAT?')
                
        #     dac.send_command('WAV:DATA?')
        #     result = dac.read_raw()
        #     values = dac.convert_raw_values(result, scale)
        #     # print(values)
        #     end = time.time() - now
        #     print(f"Data fetched in {end:.3f} seconds")
            
        #     decimal_values.extend(values)
        #     line.set_data(range(len(decimal_values)), decimal_values)
        #     ax.relim()
        #     ax.autoscale_view()
        #     dac.close()
        #     return line,
        
        # print(decimal_values)
        
        # try:
        #     ani = FuncAnimation(fig, update, interval=1, blit=True, cache_frame_data=False)
        #     plt.show()
        # except KeyboardInterrupt:
        #     dac.send_command('STOP')
        #     dac.close()
        # except:
        #     dac.send_command('STOP')
        #     dac.close()
                
        # try:
        #     while True:
        #         # if "EPTY" in status:
        #         #     # print("OK Ready to capture")
        #         #     pass
        #         # else:
        #         #     dac.send_command('STOP')
    
    
        #         while "DATA" not in status:
        #             status = dac.query('WAV:STAT?')
                    
        #         # dac.send_command('STOP')
        #         now = time.time()
        #         dac.send_command('WAV:DATA?')
        #         result = dac.read_raw()
        #         values = dac.convert_raw_values(result)
        #         end = time.time() - now
        #         # print(values)
        #         print(end)
        # except KeyboardInterrupt:
        #     dac.send_command('STOP')
        #     dac.close()
                
        # test = bitstring.BitArray(result[11:12] + result[10:11]).bin
        # print(test)
        # print(test)
        # print(int(test, 2))
        # if test[0:1] == '0':
        #     print(((((int(test, 2))/65536)) + 0.5) * 10)
        #     print("toto")
        # else:
        #     print(((((int(test[1:], 2))/65536))) * 10)
        #     print("tata")
        
        # print(result[10:12])
        # print(result[12:14])
        
        # print(result[11:12] + result[10:11])
        # print(type(result))

        
        # Lire la sortie de tension sur le canal 1
        # now = time.time()
        # future = now + 1
        # step = 0
        # while time.time() < future:
        #     
        #     step += 1
        # print(str(int(step / 1)) + " steps per second")
            
        
        
        
        # print(f"Tension de sortie sur le canal 1 : {voltage} V")

    # except Exception as e:
    #     print(f"Une erreur s'est produite : {e}")

    finally:
        dac.close()