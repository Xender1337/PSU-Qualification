import time
import numpy as np
from inputimeout import inputimeout 
import matplotlib.pyplot as plt
from GetDataWaveform import LeCroyOscilloscope
from Load import SiglentSDL1020

if __name__ == "__main__":
    # ------------------------------------- Connect to the instuments --------#

    # Define instruments address
    osc_ip = "192.168.137.49"  # Remplacez par l'adresse IP réelle de votre oscilloscope LeCroy
    osc = LeCroyOscilloscope(osc_ip)

    sdl_ip = "192.168.1.179"  # Remplacez par l'adresse IP réelle de votre SDL1020
    sdl = SiglentSDL1020(sdl_ip)

    # ------------------------------------- Define tests conditions ----------#
    # Measure ripple at different current load (A)
    steps = [0, 0.1, 1, 3]

    # ------------------------------------- Waveform acquisition -------------#
    osc.connect()
    sdl.connect()
    channel = 1  # Canal à lire 
    
    # Choose to ask an internal cal or not
    try:    
        want_cal = inputimeout('Do you want to proceed a cal of the scope ? (YES / NO, y/n) : ', 2)
    except Exception: 
        want_cal = 'n'
        print("no Cal per default") 
    
    if "y" in want_cal or "YES" in want_cal :
        osc.ask_cal()
        osc.arm() 
    

        
    for a_step in steps:
        
        sdl.set_current(a_step)
    
        sdl.enable_output(True) # Active la sortie
        # Configuration des paramètres de test
        print("Start test at {} A".format(a_step))
        
        time.sleep(0.5)

        osc.force()
        osc.restore_previous_trig_sel()
        time.sleep(1) # Make sure the oscilloscope is ready to capture

        waveform, infos = osc.get_waveform(channel)
    
        time.sleep(2)
        
        # # Désactiver la sortie
        sdl.enable_output(False)
    
        # ------------------------------------- Display Waveform  ----------------#
        
        # Générer l'axe du temps
        time_axis = np.arange(len(waveform)) * infos["time_per_point"]
        
        fig, ax = plt.subplots()
        

        volt_plot = ax.plot(time_axis, waveform, 'k', label="Voltage")
        
        # Add legend to the figure
        ax.legend(loc=0)
        
  
        ax.grid(True, linestyle='-.')
        
        # Set the params fonts, colors, size
        ax.tick_params(labelcolor='k', labelsize='medium', width=3)
        
        # Delimit the horizontal axis to display properly the result plot 
        # fig.set_xlim(0,10)
        # fig.set_ylim(0,10)
        ax.set_xlim(0, infos["time_per_point"]*infos["total_pnt"])
        ax.set_ylim((infos["min_value"] * infos["vertical_gain"]),(infos["vertical_gain"] * infos['max_value']))

        # Add to the plot the X & Y axis key name (Time and Voltage)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Voltage (V)')
        
        fig.text(0.5, -0.05,'Ripple at : {} A'.format(a_step),horizontalalignment='center')        
        # Set the expected resolution of the plot
        plt.rcParams['figure.dpi'] = 300
        plt.rcParams['savefig.dpi'] = 300
        
        plt.rcParams["axes.edgecolor"] = "black"
        plt.rcParams["axes.linewidth"] = 1
        
        # Display the result
        plt.show()
        
        
        # ------------------------------------- Compute values from the Waveform -#
        
        PeakToPeak = np.ptp(waveform)
        RMS = np.sqrt(np.mean(waveform**2))
        
        print("Peak to Peak (V) : ", PeakToPeak)
        print("Peak to Peak (mV) : {:.3f}".format((PeakToPeak * 1000)))
        print("RMS (V) : ", RMS)
        print("RMS (mV) : {:.3f}".format((RMS * 1000)))

    osc.close()
    sdl.close()
    