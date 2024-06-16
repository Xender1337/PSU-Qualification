import pyvisa
import numpy as np
import matplotlib.pyplot as plt
import time

class LeCroyOscilloscope:
    def __init__(self, ip_address):
        self.ip_address = ip_address
        self.resource_manager = pyvisa.ResourceManager('@py')
        self.instrument = None

    def connect(self):
        self.instrument = self.resource_manager.open_resource(f'TCPIP0::{self.ip_address}::inst0::INSTR')

    def send_command(self, command):
        self.instrument.write(command)

    def query(self, command):
        return self.instrument.query(command)

    def query_binary_values(self, command, datatype='h', is_big_endian=True):
        return self.instrument.query_binary_values(command, datatype=datatype, is_big_endian=is_big_endian)

    def get_waveform(self, channel):
        # Select the channel and request the waveform data

            
        self.send_command(f"C{channel}:WF? DAT1")
    

        # Query waveform data
        response = self.query_binary_values(f"C{channel}:WF? DAT1", datatype='h', is_big_endian=True)

        # Query waveform preamble
        preamble = self.query(f"C{channel}:INSPECT? WAVEDESC")
        # print(preamble)
        # Process the preamble to get the time scale
        
        time_scale = self.parse_preamble(preamble)
        
        return np.array(response), time_scale

    def parse_preamble(self, preamble):
        try :
            # print(preamble)
            # Extract the necessary parameters from the preamble
            lines = preamble.split('\n')
            time_per_point = None
            for line in lines:
                if "HORIZ_INTERVAL" in line:
                    # print(line)
                    time_per_point = float(line.split(':')[1].strip())
                    # print(time_per_point)
                    break
            return time_per_point
        except :
            osc.close()

    def close(self):
        if self.instrument:
            self.instrument.close()

if __name__ == "__main__":
    osc_ip = "192.168.137.49"  # Remplacez par l'adresse IP réelle de votre oscilloscope LeCroy
    osc = LeCroyOscilloscope(osc_ip)

    try:
        osc.connect()
        channel = 1  # Canal à lire
        index = 0
        start_time = time.time()     
        while index < 10:
            waveform, time_scale = osc.get_waveform(channel)
            
            
            # Générer l'axe du temps
            time_axis = np.arange(len(waveform)) * time_scale
    
            # Tracer la courbe
            plt.plot(time_axis, waveform)
            plt.xlabel('Temps (s)')
            plt.ylabel('Tension (V)')
            plt.title(f'Courbe du canal {channel}')
            plt.show()
            
            index = index + 1 
        end_time = time.time()     
        print('total time (sec) : ', end_time - start_time)
        print('waveform per sec : ', (1 * 10 / (end_time - start_time)))
        osc.close()
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
        osc.close()

        