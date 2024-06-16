import pyvisa

class SiglentSDL1020:
    def __init__(self, ip_address):
        self.ip_address = ip_address
        self.resource_manager = pyvisa.ResourceManager('@py')
        self.instrument = None

    def connect(self):
        self.instrument = self.resource_manager.open_resource(f'TCPIP0::{self.ip_address}::inst0::INSTR')
        print(f"Connected to: {self.instrument.query('*IDN?')}")

    def send_command(self, command):
        self.instrument.write(command)

    def query(self, command):
        return self.instrument.query(command)

    def set_current(self, current):
        self.send_command(f'CURR {current}')

    def set_voltage(self, voltage):
        self.send_command(f'VOLT {voltage}')

    def measure_current(self):
        return float(self.query('MEAS:CURR?'))

    def measure_voltage(self):
        return float(self.query('MEAS:VOLT?'))

    def enable_output(self, enable=True):
        state = 'ON' if enable else 'OFF'
        self.send_command(f':SOURce:INPut:STATe {state}')

    def close(self):
        if self.instrument:
            self.instrument.close()

