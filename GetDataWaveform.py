import pyvisa
import time
import numpy as np

class LeCroyOscilloscope:
    def __init__(self, ip_address):
        self.ip_address = ip_address
        self.resource_manager = pyvisa.ResourceManager('@py')
        self.instrument = None
        self.previous_state_before_force = None

    def connect(self):
        self.instrument = self.resource_manager.open_resource(f'TCPIP0::{self.ip_address}::inst0::INSTR')

    def send_command(self, command):
        self.instrument.write(command)
        
    def arm(self):
        self.send_command('*TRG')
        
    def force(self):
        self.previous_state_before_force = self.get_current_trig_sel()
        # print("Trig was forced by changing the trig selectection. Previous state was : ", self.previous_state_before_force)
        self.send_command('TRMD STOP;ARM;FRTR')
        time.sleep(2)
        
    def restore_previous_trig_sel(self):
        self.set_trig_sel(self.previous_state_before_force)
        
    def get_current_trig_sel(self):
        return self.query('TRIG_SELECT?')
        
    def set_trig_sel(self, trig_sel):
        return self.send_command(trig_sel)
        
    def ask_cal(self):
        self.send_command("*CAL?")
        print('Wait for a complete calibration before measurement ...\n', end="\r")
        # Add a timer to let the scope make is complete calibration and let the waveform for settling time
        t = 8
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
            result.append((a_value * infos["vertical_gain"]) - infos["vertical_offset"])
        # print(response)
        # print(result)
        # print(len(result))
        
        return np.array(result), infos

    def parse_preamble(self, preamble):
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
            if "MAX_VALUE" in line:
                waveform_infos["max_value"] = float(line.split(':')[1].strip())
            if "MIN_VALUE" in line:
                waveform_infos["min_value"] = float(line.split(':')[1].strip())
            if "HORIZ_OFFSET" in line:
                waveform_infos["horiz_offset"] = float(line.split(':')[1].strip())
            if "VERTICAL_OFFSET" in line:
                waveform_infos["vertical_offset"] = float(line.split(':')[1].strip())
        # print(preamble)
        return waveform_infos


    def close(self):
        if self.instrument:
            self.instrument.close()

