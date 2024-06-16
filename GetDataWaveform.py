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
        
    def ask_cal(self):
        self.send_command("*CAL?")
        print('Wait for a complete calibration before measurement ... : \n', end="\r")
        # Add a timer to let the scope make is complete calibration and let the waveform for settling time
        t = 7
        while t:
            time.sleep(1)
            t -= 1
            print('\r{}'.format(t), end='', flush=True)
        print("\nAutocal complete !")
        
    def query(self, command):
        return self.instrument.query(command)

    def query_binary_values(self, command, datatype='h', is_big_endian=True):
        return self.instrument.query_binary_values(command, datatype=datatype, is_big_endian=is_big_endian)

    def get_waveform(self, channel):
        # Select the channel and request the waveform data
        self.send_command(f"C{channel}:WF? DAT1")
    
        # Query waveform data
        response = self.query_binary_values(f"C{channel}:WF? DAT1", datatype='b', is_big_endian=True)

        # Query waveform preamble
        preamble = self.query(f"C{channel}:INSPECT? WAVEDESC")
        # Process the preamble to get the time scale
        
        infos = self.parse_preamble(preamble)
        
        # Convert ADC value to Physical value (V/A/W...)
        
        result = list()
        for a_value in response:
            result.append(a_value * infos["vertical_gain"])
        # print(response)
        # print(result)
        # print(len(result))
        
        return np.array(result), infos

    def parse_preamble(self, preamble):
        try :
            # print(preamble)
            # Extract the necessary parameters from the preamble
            lines = preamble.split('\n')
            
            waveform_infos = dict()
            for line in lines:
                # Timebase
                if "TIMEBASE" in line:
                    waveform_infos["timebase"] = line.split(':')[1].strip()
                if "HORIZ_INTERVAL" in line:
                    waveform_infos["time_per_point"] = float(line.split(':')[1].strip())
                if "PNTS_PER_SCREEN" in line:
                    waveform_infos["total_pnt"] = float(line.split(':')[1].strip())
                if "VERTICAL_GAIN" in line:
                    waveform_infos["vertical_gain"] = float(line.split(':')[1].strip())
            # print(preamble)
            return waveform_infos
        except :
            osc.close()

    def close(self):
        if self.instrument:
            self.instrument.close()

if __name__ == "__main__":
    osc_ip = "192.168.137.49"  # Remplacez par l'adresse IP réelle de votre oscilloscope LeCroy
    osc = LeCroyOscilloscope(osc_ip)


    # ------------------------------------- Waveform acquisition -------------#

    # try:
    osc.connect()
    channel = 1  # Canal à lire 
    
    osc.ask_cal()

    waveform, infos = osc.get_waveform(channel)
    osc.close()

    
    # ------------------------------------- Display Waveform  ----------------#
    
    # Générer l'axe du temps
    time_axis = np.arange(len(waveform)) * infos["time_per_point"]
    
    fig, ax = plt.subplots()
    ax.plot(time_axis, waveform)
    ax.grid(True, linestyle='-.')
    ax.tick_params(labelcolor='r', labelsize='medium', width=3)
    ax.set_xlim(0, infos["time_per_point"]*infos["total_pnt"])
    
    # plt.plot(time_axis, waveform)
    plt.xlabel('Temps (s)')
    plt.ylabel('Tension (V)')
    # plt.title(f'Courbe du canal {channel}')
    # plt.grid(True, linestyle='--', which='both', axis='both', color='gray', alpha=0.5)
    
    plt.rcParams['figure.dpi'] = 300
    plt.rcParams['savefig.dpi'] = 300
    plt.show()
    
    
    # ------------------------------------- Compute values from the Waveform -#
    
    PeakToPeak = np.ptp(waveform)
    RMS = np.sqrt(np.mean(waveform**2))
    
    print("Peak to Peak (V) : ", PeakToPeak)
    print("Peak to Peak (mV) : {:.3f}".format((PeakToPeak * 1000)))
    print("Peak to Peak (V) : ", RMS)
    print("Peak to Peak (mV) : {:.3f}".format((RMS * 1000)))
    # except Exception as e:
    #     print(f"Une erreur s'est produite : {e}")
    #     osc.close()
