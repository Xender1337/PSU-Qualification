import pyvisa
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button
import threading
import queue

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

class DataAcquisitionThread(threading.Thread):
    def __init__(self, daq, data_queue, scanlist, scale):
        super().__init__()
        self.daq = daq
        self.data_queue = data_queue
        self.scanlist = scanlist
        self.scale = scale
        self.running = threading.Event()
        self.running.set()

    def run(self):
        while self.running.is_set():
            if "DATA" in self.daq.query('WAV:STAT?'):
                self.daq.send_command('WAV:DATA?')
                result = self.daq.read_raw()
                values = self.daq.convert_raw_values(result, self.scale)
                self.data_queue.put(values)
            time.sleep(0.001)

    def pause(self):
        self.daq.send_command('STOP')
        self.running.clear()

    def resume(self):
        self.daq.send_command('RUN')
        self.running.set()

    def stop(self):
        self.running.clear()
        self.daq.send_command('STOP')
        if "DATA" in self.daq.query('WAV:STAT?'):
            self.daq.send_command('WAV:DATA?')
            self.daq.read_raw()

def update_plot(frame, y_data, lines, data_queue, sampling_rate):
    if update_plot.pause:
        ax.relim()
        ax.autoscale_view()
        frame.canvas.draw()
        frame.canvas.flush_events()

        return lines

    if not data_queue.empty():
        while not data_queue.empty():
            values = data_queue.get()
            # print(values)
            for i, line in enumerate(lines):
                y_data[i].extend(values[i])
                if len(y_data[i]) > 200000:
                    y_data[i] = y_data[i][-200000:]
    
                # Convert the x-axis to milliseconds
                x_data = np.arange(len(y_data[i])) / sampling_rate * 1000
                line.set_data(x_data, y_data[i])
            
    else:
        ax.relim()
        ax.autoscale_view()
        frame.canvas.draw()
        frame.canvas.flush_events()

    return lines

update_plot.pause = False

def on_pause(event):
    update_plot.pause = not update_plot.pause
    if update_plot.pause:
        pause_button.label.set_text('Resume')
        daq_thread.pause()
    else:
        pause_button.label.set_text('Pause')
        daq_thread.resume()

if __name__ == "__main__":
    usb_address = "USB0::0x0957::0x1118::TW47031015::0::INSTR"  # Replace with actual USB address
    dac = KeysightDAC(usb_address)
    data = []
    lines = []
    data_queue = queue.Queue()

    dac.connect()
    print(dac.measure_output(101))
    dac.define_sampling_rate(25000)  # 40 Ks/s
    dac.define_sample_points(5000)
    
    scanlist = [dac.ANALOG_CHANNEL_1, dac.ANALOG_CHANNEL_2, dac.ANALOG_CHANNEL_3, dac.ANALOG_CHANNEL_4, dac.ANALOG_CHANNEL_5, dac.ANALOG_CHANNEL_6]
    dac.configure_scanlist(scanlist)
    
    print(dac.get_sampling_points())
    print(dac.get_sampling_rate())
    
    time.sleep(0.5)
    for channel in scanlist:
        dac.configure_output(channel, dac.VOLTAGE_RANGE_5V, dac.CHANNEL_UNIPOLAR_MODE)

    dac.send_command('RUN')
    
    while "DATA" not in dac.query('WAV:STAT?'):
        time.sleep(0.1)

    sampling_rate = dac.get_sampling_rate()

    daq_thread = DataAcquisitionThread(dac, data_queue, scanlist, dac.VOLTAGE_RANGE_5V)
    daq_thread.start()

    fig, ax = plt.subplots()
    
    for _ in scanlist:
        line, = ax.plot([], [], lw=1)
        lines.append(line)
        data.append([])

    ax.grid()

    # Add the pause button
    ax_pause = plt.axes([0.81, 0.01, 0.1, 0.075])
    pause_button = Button(ax_pause, 'Pause')
    pause_button.on_clicked(on_pause)

    # ani = FuncAnimation(fig, update_plot, fargs=(data, lines, data_queue, sampling_rate), blit=False, interval=5)
    
    plt.show()
        
    try:
        while True:
            # print('running')
            time.sleep(0.005)
            # if not data_queue.empty():
            # now = time.time()
            lines = update_plot(fig, data, lines, data_queue, sampling_rate)
            # end = time.time() - now
            # print(data_queue.qsize())
            # print(end)  
    except BaseException:
        print('error')            
    except KeyboardInterrupt():
        daq_thread.stop()
        daq_thread.join()
        dac.close()
        
    daq_thread.stop()
    daq_thread.join()
    dac.close()
