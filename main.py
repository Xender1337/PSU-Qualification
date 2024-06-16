import time
import numpy as np
import matplotlib.pyplot as plt
from GetDataWaveform import LeCroyOscilloscope
from Load import SiglentSDL1020

if __name__ == "__main__":
    osc_ip = "192.168.137.49"  # Remplacez par l'adresse IP réelle de votre oscilloscope LeCroy
    osc = LeCroyOscilloscope(osc_ip)

    sdl_ip = "192.168.1.179"  # Remplacez par l'adresse IP réelle de votre SDL1020
    sdl = SiglentSDL1020(sdl_ip)

    # ------------------------------------- Waveform acquisition -------------#

    # try:
    osc.connect()
    sdl.connect()
    channel = 1  # Canal à lire 
    
    # Choose to ask an internal cal or not
    want_cal = input('Do you want to proceed a cal of the scope ? (YES / NO, y/n) : ')
    if "y" in want_cal or "YES" in want_cal :
        osc.ask_cal()
    
    osc.arm()
    
    time.sleep(2)

    # Configuration des paramètres de test
    # sdl.set_voltage(12.0)  # Définit la tension à 12V
    sdl.set_current(0.5)   # Définit le courant à 1A

    sdl.enable_output(True) # Active la sortie
    
    time.sleep(2)
    
    waveform, infos = osc.get_waveform(channel)
    osc.close()

    # # Désactiver la sortie
    sdl.enable_output(False)

    # ------------------------------------- Display Waveform  ----------------#
    
    # Générer l'axe du temps
    time_axis = np.arange(len(waveform)) * infos["time_per_point"]
    
    fig, ax = plt.subplots()
    ax.plot(time_axis, waveform, 'r')
    ax.grid(True, linestyle='-.')
    
    # Set the params fonts, colors, size
    ax.tick_params(labelcolor='b', labelsize='medium', width=3)
    
    # Delimit the horizontal axis to display properly the result plot 
    ax.set_xlim(0, infos["time_per_point"]*infos["total_pnt"])
    
    # Add to the plot the X & Y axis key name (Time and Voltage)
    plt.xlabel('Temps (s)')
    plt.ylabel('Tension (V)')
    
    # Set the expected resolution of the plot
    plt.rcParams['figure.dpi'] = 300
    plt.rcParams['savefig.dpi'] = 300
    
    # Display the result
    plt.show()
    
    
    # ------------------------------------- Compute values from the Waveform -#
    
    PeakToPeak = np.ptp(waveform)
    RMS = np.sqrt(np.mean(waveform**2))
    
    print("Peak to Peak (V) : ", PeakToPeak)
    print("Peak to Peak (mV) : {:.3f}".format((PeakToPeak * 1000)))
    print("Peak to Peak (V) : ", RMS)
    print("Peak to Peak (mV) : {:.3f}".format((RMS * 1000)))
