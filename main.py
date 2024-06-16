import numpy as np
import matplotlib.pyplot as plt
from GetDataWaveform import LeCroyOscilloscope

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
