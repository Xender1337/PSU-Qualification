import pyvisa
import time

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

if __name__ == "__main__":
    sdl_ip = "192.168.1.179"  # Remplacez par l'adresse IP réelle de votre SDL1020
    sdl = SiglentSDL1020(sdl_ip)

    try:
        sdl.connect()
        
        # Configuration des paramètres de test
        # sdl.set_voltage(12.0)  # Définit la tension à 12V
        sdl.set_current(0.5)   # Définit le courant à 1A
        sdl.enable_output(True) # Active la sortie

        # Attendre quelques secondes pour stabilisation
        time.sleep(5)
        
        # Mesurer les valeurs de tension et de courant
        voltage = sdl.measure_voltage()
        current = sdl.measure_current()
        
        print(f"Mesure de la tension : {voltage} V")
        print(f"Mesure du courant : {current} A")

        # # Désactiver la sortie
        sdl.enable_output(False)

    except Exception as e:
        print(f"Une erreur s'est produite : {e}")

    finally:
        sdl.close()