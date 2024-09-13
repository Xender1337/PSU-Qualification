import time
import subprocess
from KeysightDAC import KeysightDAC as pydaq

def acquire_data_real_time(duration, sample_rate):
    usb_address = "USB0::0x0957::0x1118::TW47031015::0::INSTR"  # Remplacez par l'adresse USB réelle de votre DAC
    daq = pydaq(usb_address)
    daq.connect()
    daq.configure_scanlist([daq.ANALOG_CHANNEL_1, daq.ANALOG_CHANNEL_2])
    daq.define_sampling_rate(sample_rate)
    daq.define_sample_points(100)
    daq.configure_output(daq.ANALOG_CHANNEL_1, daq.VOLTAGE_RANGE_5V, daq.CHANNEL_UNIPOLAR_MODE)
    daq.configure_output(daq.ANALOG_CHANNEL_2, daq.VOLTAGE_RANGE_5V, daq.CHANNEL_UNIPOLAR_MODE)
    daq.start_acquisition()

    start_time = time.time()
    vcd_data = "$date today $end\n"
    vcd_data += "$version DAQ U2351A to VCD $end\n"
    vcd_data += "$timescale 1 us $end\n"
    vcd_data += "$scope module signals $end\n"
    vcd_data += "$var wire 1 a signal1 $end\n"
    vcd_data += "$var wire 1 b signal2 $end\n"
    vcd_data += "$upscope $end\n"
    vcd_data += "$enddefinitions $end\n"

    timestamp = 0

    while time.time() - start_time < duration:
        status = daq.query('WAV:STAT?')
        print(status)
        if "DATA" in status:
            daq.send_command('WAV:DATA?')
            result = daq.read_raw()
            channels_values = daq.convert_raw_values(result, daq.VOLTAGE_RANGE_5V)
            
            Channel_nbr = len(channels_values)
            Value_nbr = len(channels_values[0])
            
            print(channels_values)
            
            
            index = 0        
            
            while index < Value_nbr:
                # print(channels_values[0][index])
                # print(channels_values[1][index])
                vcd_data += f"#{timestamp}\n"
                vcd_data += f"b{channels_values[0][index]} a\n"
                vcd_data += f"b{channels_values[1][index]} a\n"
                timestamp += 1
                index += 1


        with open('output.sr', 'w') as f:
            f.write(vcd_data)

        time.sleep(1.0 / sample_rate)

    daq.stop_acquisition()

def visualize_vcd():
    subprocess.run(['sigrok-cli', '-i', 'output.vcd', '-o', 'output.sr'])

# Paramètres d'acquisition
duration = 50  # Durée en secondes
sample_rate = 100  # Taux d'échantillonnage en Hz

# Acquisition et visualisation
# visualize_vcd()
acquire_data_real_time(duration, sample_rate)
