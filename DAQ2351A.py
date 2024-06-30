import pyvisa
import bitstring
import time
import numpy as np

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
        self.send_command("ACQuire:SRATe {}".format(rate)) # rate shall be in Hertz
        
    def define_sample_points(self, number_of_points):
        self.send_command("WAV:POIN {}".format(number_of_points))

    def close(self):
        if self.instrument:
            self.instrument.close()
            
    # def convert_raw_values(self, raw_values):
    #     byte_nbr = int(raw_values[2:10].decode()) # get the nuber of byte
    #     index = 10 # start the index at 10
        
    #     while 10 + byte_nbr > index:
    #         if index == byte_nbr:
    #             break
    #         bit_value = bitstring.BitArray(raw_values[index + 1: index + 2] + raw_values[index: index + 1]).bin
    #         print(bit_value)
            
    #         if bit_value[0:1] == '0':
    #             decimal_value = ((((int(bit_value, 2))/65536)) + 0.5) * 10
    #             print(decimal_value)
    #         else:
    #             decimal_value = ((((int(bit_value[1:], 2))/65536))) * 10
    #             print(decimal_value)
    #         index = index + 2
    
    # def convert_raw_values(self, raw_values):
    #     byte_nbr = int(raw_values[2:10].decode())  # get the number of bytes
    #     index = 10  # start the index at 10
    
    #     while index < 10 + byte_nbr:
    #         # Combine the two bytes, reversing their order and converting to a bitstring
    #         bit_value = format((raw_values[index + 1] << 8) | raw_values[index], '016b')
    
    #         # Convert bitstring to decimal value
    #         if bit_value[0] == '0':
    #             decimal_value = ((int(bit_value, 2) / 65536) + 0.5) * 10
    #         else:
    #             decimal_value = (int(bit_value[1:], 2) / 65536) * 10
            
    #         index += 2
            
    def convert_raw_values(self, raw_values):
        byte_nbr = int(raw_values[2:10].decode())  # Get the number of bytes
        index = 10  # Start the index at 10
    
        while index < 10 + byte_nbr:
            # Combine the two bytes, reversing their order
            combined_value = (raw_values[index + 1] << 8) | raw_values[index]
            
            # Check the sign bit (most significant bit)
            if combined_value & 0x8000 == 0:
                # Positive value
                decimal_value = ((combined_value / 65536) + 0.5) * 10
            else:
                # Negative value, use only the lower 15 bits
                decimal_value = ((combined_value & 0x7FFF) / 65536) * 10
            
            index += 2

if __name__ == "__main__":
    usb_address = "USB0::0x0957::0x0F18::TW50200512::0::INSTR"  # Remplacez par l'adresse USB réelle de votre DAC
    dac = KeysightDAC(usb_address)

    try:
        dac.connect()
        print(dac.measure_output(101))
        dac.define_sampling_rate(250000) #  500Ks/s
        dac.define_sample_points(100000)
        
        # print(dac.measure_output(101))
        # dac.define_sampling_rate(250) #  500Ks/s
        # dac.define_sample_points(10)
        # dac.send_command('DIG')
        
        time.sleep(0.5)
        dac.send_command('ROUT:CHAN:POL UNIP,(@101)')
        # dac.send_command('VOLT:RANG 5,(@101)') # define voltage range @+/-5V
        print(dac.query('ROUT:CHAN:POL? (@101)'))
        time.sleep(0.5)
        dac.send_command('ROUT:CHAN:RANG 10,(@101)') # define voltage range @+/-5V
        print(dac.query('ROUT:CHAN:RANG? (@101)'))
        time.sleep(0.5)
        dac.send_command('RUN')
        status = dac.query('WAV:STAT?')
        
        # if "EPTY" in status:
        #     # print("OK Ready to capture")
        #     pass
        # else:
        #     dac.send_command('STOP')


        while "DATA" not in status:
            status = dac.query('WAV:STAT?')
            
        dac.send_command('STOP')
        now = time.time()
        dac.send_command('WAV:DATA?')
        result = dac.read_raw()
        values = dac.convert_raw_values(result)
        end = time.time() - now
        # print(values)
        print(end)
        
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

    except Exception as e:
        print(f"Une erreur s'est produite : {e}")

    finally:
        dac.close()